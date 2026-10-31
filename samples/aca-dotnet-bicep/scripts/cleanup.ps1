<#
.SYNOPSIS
    Elimina el grupo de recursos y todo lo que contiene. No se puede deshacer.
#>
param(
    [string]$ResourceGroup = "rg-aca-dotnet-sample"
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

Write-Host "Eliminando el grupo de recursos '$ResourceGroup' (en segundo plano)..." -ForegroundColor Yellow
az group delete --name $ResourceGroup --yes --no-wait
Write-Host "Listo. Comprueba el avance con: az group show -n $ResourceGroup"
