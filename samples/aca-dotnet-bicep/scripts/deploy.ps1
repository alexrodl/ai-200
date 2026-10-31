<#
.SYNOPSIS
    Despliega el ejemplo completo: infraestructura (Bicep), imágenes (ACR) y container apps.

.EXAMPLE
    ./scripts/deploy.ps1
    ./scripts/deploy.ps1 -ResourceGroup rg-aca-demo -Location eastus2
    ./scripts/deploy.ps1 -SkipInfra     # solo recompila las imágenes y actualiza las apps
#>
param(
    [string]$ResourceGroup = "rg-aca-dotnet-sample",
    [string]$Location = "centralus",
    [string]$ImageTag = (Get-Date -Format "yyyyMMddHHmmss"),
    [switch]$SkipInfra
)

$ErrorActionPreference = "Stop"
# Si un comando 'az' falla, el script se detiene en lugar de seguir con el siguiente paso.
$PSNativeCommandUseErrorActionPreference = $true

$root = Split-Path $PSScriptRoot -Parent

function Write-Step([string]$Text) {
    Write-Host "`n==> $Text" -ForegroundColor Cyan
}

Write-Step "Comprobando la sesión de Azure CLI"
$account = az account show -o json | ConvertFrom-Json
Write-Host "Suscripción: $($account.name) ($($account.id))"

if (-not $SkipInfra) {
    Write-Step "Registrando los proveedores de recursos (solo la primera vez tarda)"
    foreach ($provider in "Microsoft.App", "Microsoft.OperationalInsights", "Microsoft.ContainerRegistry", "Microsoft.ServiceBus", "Microsoft.DocumentDB", "Microsoft.CognitiveServices") {
        az provider register --namespace $provider --wait -o none
    }

    Write-Step "1/4 Grupo de recursos '$ResourceGroup' en $Location"
    az group create --name $ResourceGroup --location $Location -o none

    # Cosmos DB free tier y Azure AI Language F0 admiten un solo recurso por suscripción.
    # Si ya existe otro en un grupo de recursos distinto, se usa la opción de pago por uso.
    $otherFreeCosmos = az cosmosdb list -o json | ConvertFrom-Json |
        Where-Object { $_.enableFreeTier -and $_.resourceGroup -ne $ResourceGroup }
    $otherFreeLanguage = az cognitiveservices account list -o json | ConvertFrom-Json |
        Where-Object { $_.kind -eq "TextAnalytics" -and $_.sku.name -eq "F0" -and $_.resourceGroup -ne $ResourceGroup }

    $cosmosFreeTier = if ($otherFreeCosmos) { "false" } else { "true" }
    $languageSku = if ($otherFreeLanguage) { "S" } else { "F0" }
    if ($otherFreeCosmos) { Write-Host "La suscripción ya usa el free tier de Cosmos DB ($($otherFreeCosmos[0].name)): se crea como serverless." -ForegroundColor Yellow }
    if ($otherFreeLanguage) { Write-Host "La suscripción ya tiene un Azure AI Language F0 ($($otherFreeLanguage[0].name)): se crea con SKU S (pago por uso)." -ForegroundColor Yellow }

    Write-Step "2/4 Infraestructura compartida (infra/core.bicep)"
    Write-Host "Log Analytics, Application Insights, ACR, Service Bus, Cosmos DB, Azure AI Language, identidades y entorno. Tarda unos minutos..."
    az deployment group create `
        --resource-group $ResourceGroup `
        --name core `
        --template-file "$root/infra/core.bicep" `
        --parameters location=$Location cosmosFreeTier=$cosmosFreeTier languageSku=$languageSku `
        -o none
}

# Las salidas de core.bicep (nombres de recursos) alimentan los pasos siguientes.
$core = az deployment group show --resource-group $ResourceGroup --name core --query properties.outputs -o json | ConvertFrom-Json

Write-Step "3/4 Compilando las imágenes en ACR '$($core.registryName.value)' (etiqueta $ImageTag)"
Write-Host "ACR compila en la nube con cada Dockerfile: no hace falta Docker instalado."
foreach ($project in "Api", "Worker", "Web") {
    $image = "$($project.ToLower()):$ImageTag"
    Write-Host "  - $image"
    az acr build `
        --registry $core.registryName.value `
        --image $image `
        --file "$root/src/$project/Dockerfile" `
        --no-logs `
        -o none `
        "$root/src/$project"
}

Write-Step "4/4 Container apps (infra/apps.bicep)"
$webUrl = az deployment group create `
    --resource-group $ResourceGroup `
    --name apps `
    --template-file "$root/infra/apps.bicep" `
    --parameters `
        environmentName=$($core.environmentName.value) `
        registryLoginServer=$($core.registryLoginServer.value) `
        serviceBusName=$($core.serviceBusName.value) `
        queueName=$($core.queueName.value) `
        appsIdentityName=$($core.appsIdentityName.value) `
        scalerIdentityName=$($core.scalerIdentityName.value) `
        appInsightsName=$($core.appInsightsName.value) `
        cosmosAccountName=$($core.cosmosAccountName.value) `
        cosmosDatabaseName=$($core.cosmosDatabaseName.value) `
        cosmosContainerName=$($core.cosmosContainerName.value) `
        languageAccountName=$($core.languageAccountName.value) `
        imageTag=$ImageTag `
    --query properties.outputs.webUrl.value `
    -o tsv

Write-Step "Listo"
Write-Host "Web:              $webUrl" -ForegroundColor Green
Write-Host "Grupo de recursos: $ResourceGroup"
Write-Host ""
Write-Host "Siguientes pasos:"
Write-Host "  ./scripts/watch.ps1            # réplicas, revisiones y mensajes en la cola en vivo"
Write-Host "  ./scripts/load-test.ps1        # carga HTTP para escalar la web"
Write-Host "  ./scripts/traffic-split.ps1    # revisión v2 con el 20 % del tráfico"
