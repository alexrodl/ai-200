<#
.SYNOPSIS
    Genera carga HTTP contra la web para ver la regla de escalado HTTP en acción.

.DESCRIPTION
    Lanza -Concurrency "usuarios virtuales" en paralelo. Cada uno llama en bucle a /simulate
    (que tarda -DelayMs en responder) durante -DurationSeconds. Al final muestra qué revisiones
    y réplicas respondieron: sirve también para comprobar la división de tráfico.

    Con la regla de la web (10 solicitudes simultáneas por réplica), 30 usuarios ~ 3 réplicas.

.EXAMPLE
    ./scripts/load-test.ps1
    ./scripts/load-test.ps1 -Concurrency 50 -DurationSeconds 180 -DelayMs 1000
#>
param(
    [string]$ResourceGroup = "rg-aca-dotnet-sample",
    [ValidateRange(1, 200)][int]$Concurrency = 30,
    [ValidateRange(10, 600)][int]$DurationSeconds = 120,
    [ValidateRange(0, 10000)][int]$DelayMs = 500
)

$ErrorActionPreference = "Stop"

$fqdn = az containerapp show --name web --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn -o tsv
$url = "https://$fqdn/simulate?delayMs=$DelayMs"
$deadline = (Get-Date).AddSeconds($DurationSeconds)

Write-Host "Carga contra $url" -ForegroundColor Cyan
Write-Host "$Concurrency usuarios en paralelo durante $DurationSeconds s. Mira las réplicas con ./scripts/watch.ps1"

$results = 1..$Concurrency | ForEach-Object -ThrottleLimit $Concurrency -Parallel {
    $hits = [System.Collections.Generic.List[string]]::new()
    while ((Get-Date) -lt $using:deadline) {
        try {
            $response = Invoke-RestMethod -Uri $using:url -TimeoutSec 30
            $hits.Add("$($response.revision)|$($response.replica)")
        }
        catch {
            $hits.Add("ERROR")
        }
    }
    $hits
}

$ok = @($results | Where-Object { $_ -ne "ERROR" })
$errors = $results.Count - $ok.Count

Write-Host "`nSolicitudes: $($results.Count)   OK: $($ok.Count)   Errores: $errors" -ForegroundColor Green

Write-Host "`nRespuestas por revisión:"
$ok | ForEach-Object { $_.Split("|")[0] } | Group-Object | Sort-Object Count -Descending |
    Format-Table @{ Name = "Revisión"; Expression = { $_.Name } },
                 @{ Name = "Solicitudes"; Expression = { $_.Count } },
                 @{ Name = "%"; Expression = { [math]::Round(100 * $_.Count / $ok.Count, 1) } } -AutoSize

Write-Host "Réplicas distintas que respondieron: $(($ok | Sort-Object -Unique).Count)"
