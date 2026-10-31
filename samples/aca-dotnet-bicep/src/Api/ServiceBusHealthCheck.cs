using Azure.Messaging.ServiceBus;
using Microsoft.Extensions.Diagnostics.HealthChecks;

namespace Api;

/// <summary>
/// Readiness: la API solo está "lista" si su sender de Service Bus está disponible.
/// Container Apps no envía tráfico a una réplica cuyo sondeo de preparación falla.
/// </summary>
public class ServiceBusHealthCheck(ServiceBusSender sender) : IHealthCheck
{
    public Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken cancellationToken = default) =>
        Task.FromResult(sender.IsClosed
            ? HealthCheckResult.Unhealthy("El sender de Service Bus está cerrado.")
            : HealthCheckResult.Healthy());
}
