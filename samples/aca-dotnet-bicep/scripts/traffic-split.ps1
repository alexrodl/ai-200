<#
.SYNOPSIS
    Despliegue progresivo de la web: crea una revisión nueva y le da solo una parte del tráfico.

.DESCRIPTION
    Pasos (los mismos que harías a mano en el portal):
      1. Fija el 100 % del tráfico en la revisión actual por su nombre.
      2. Crea una revisión nueva con otra APP_VERSION (la banda de la página cambia de color).
      3. Espera a que la revisión nueva esté sana.
      4. Reparte el tráfico, por ejemplo 80/20.

.EXAMPLE
    ./scripts/traffic-split.ps1
    ./scripts/traffic-split.ps1 -NewVersion v3 -NewWeight 50
#>
param(
    [string]$ResourceGroup = "rg-aca-dotnet-sample",
    [string]$NewVersion = "v2",
    [ValidateRange(1, 100)][int]$NewWeight = 20
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$app = "web"

function Write-Step([string]$Text) {
    Write-Host "`n==> $Text" -ForegroundColor Cyan
}

Write-Step "Revisión que recibe más tráfico hoy"
$revisions = az containerapp revision list --name $app --resource-group $ResourceGroup -o json | ConvertFrom-Json
$current = $revisions |
    Where-Object { $_.properties.trafficWeight -gt 0 } |
    Sort-Object { $_.properties.trafficWeight } -Descending |
    Select-Object -First 1
Write-Host $current.name

Write-Step "1/4 Fijando el 100 % del tráfico en $($current.name)"
# Sin este paso, la regla 'latestRevision' le daría el 100 % a la revisión nueva apenas esté lista.
az containerapp ingress traffic set --name $app --resource-group $ResourceGroup `
    --revision-weight latest=0 "$($current.name)=100" -o none

Write-Step "2/4 Creando una revisión nueva con APP_VERSION=$NewVersion"
$suffix = "$($NewVersion.ToLower())-$(Get-Date -Format HHmmss)"
$newRevision = "$app--$suffix"
az containerapp update --name $app --resource-group $ResourceGroup `
    --revision-suffix $suffix `
    --set-env-vars "APP_VERSION=$NewVersion" -o none
Write-Host $newRevision

Write-Step "3/4 Esperando a que $newRevision esté sana"
$timeout = (Get-Date).AddMinutes(5)
do {
    Start-Sleep -Seconds 5
    $revision = az containerapp revision show --name $app --resource-group $ResourceGroup --revision $newRevision -o json | ConvertFrom-Json
    $running = $revision.properties.runningState
    $health = $revision.properties.healthState
    Write-Host "  runningState=$running healthState=$health"

    if ($running -in "Failed", "Degraded") {
        throw "La revisión $newRevision no arrancó. Revisa: az containerapp logs show -n $app -g $ResourceGroup --revision $newRevision"
    }
    if ((Get-Date) -gt $timeout) {
        throw "Tiempo de espera agotado. La revisión $newRevision no quedó sana en 5 minutos."
    }
} until ($health -eq "Healthy")

Write-Step "4/4 Repartiendo el tráfico: $($current.name) $(100 - $NewWeight) % / $newRevision $NewWeight %"
az containerapp ingress traffic set --name $app --resource-group $ResourceGroup `
    --revision-weight "$($current.name)=$(100 - $NewWeight)" "$newRevision=$NewWeight" -o none
az containerapp ingress traffic show --name $app --resource-group $ResourceGroup -o table

Write-Host ""
Write-Host "Recarga la página varias veces o ejecuta ./scripts/load-test.ps1 para ver el reparto."
Write-Host ""
Write-Host "Promover la versión nueva al 100 %:"
Write-Host "  az containerapp ingress traffic set -n $app -g $ResourceGroup --revision-weight $newRevision=100 $($current.name)=0"
Write-Host "Volver atrás (rollback):"
Write-Host "  az containerapp ingress traffic set -n $app -g $ResourceGroup --revision-weight $($current.name)=100 $newRevision=0"
Write-Host "Desactivar la revisión que ya no recibe tráfico:"
Write-Host "  az containerapp revision deactivate -n $app -g $ResourceGroup --revision <nombre>"
