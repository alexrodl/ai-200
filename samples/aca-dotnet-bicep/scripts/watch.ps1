<#
.SYNOPSIS
    Muestra en vivo las revisiones activas, réplicas y tráfico de cada app, más los mensajes en la cola.
    Ideal para dejarlo corriendo en una segunda terminal durante la demo. Ctrl+C para salir.
#>
param(
    [string]$ResourceGroup = "rg-aca-dotnet-sample",
    [int]$IntervalSeconds = 5
)

$ErrorActionPreference = "Stop"

$core = az deployment group show --resource-group $ResourceGroup --name core --query properties.outputs -o json | ConvertFrom-Json
$serviceBus = $core.serviceBusName.value
$queue = $core.queueName.value

while ($true) {
    $rows = foreach ($app in "web", "api", "worker") {
        $revisions = az containerapp revision list --name $app --resource-group $ResourceGroup -o json | ConvertFrom-Json
        foreach ($revision in $revisions | Where-Object { $_.properties.active }) {
            [pscustomobject]@{
                App      = $app
                Revision = $revision.name
                Replicas = $revision.properties.replicas
                Traffic  = if ($null -ne $revision.properties.trafficWeight) { "$($revision.properties.trafficWeight) %" } else { "-" }
                Health   = $revision.properties.healthState
            }
        }
    }

    $pending = az servicebus queue show --resource-group $ResourceGroup --namespace-name $serviceBus --name $queue `
        --query countDetails.activeMessageCount -o tsv

    Clear-Host
    Write-Host "Container Apps - $ResourceGroup   $(Get-Date -Format T)   (Ctrl+C para salir)" -ForegroundColor Cyan
    $rows | Format-Table -AutoSize | Out-Host
    Write-Host "Mensajes pendientes en la cola '$queue': $pending" -ForegroundColor Yellow

    Start-Sleep -Seconds $IntervalSeconds
}
