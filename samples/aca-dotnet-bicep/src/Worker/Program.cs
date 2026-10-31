using Azure.AI.TextAnalytics;
using Azure.Core;
using Azure.Identity;
using Azure.Messaging.ServiceBus;
using Azure.Monitor.OpenTelemetry.AspNetCore;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Worker;

// El worker no recibe tráfico (no tiene ingress), pero levanta un servidor HTTP mínimo
// para exponer los sondeos de liveness y readiness que usa Container Apps.
var builder = WebApplication.CreateBuilder(args);

var serviceBusFqdn = Required(builder.Configuration, "SERVICEBUS_FQDN");
var options = new ProcessingOptions(
    QueueName: builder.Configuration["SERVICEBUS_QUEUE"] ?? "jobs",
    MaxConcurrentCalls: builder.Configuration.GetValue("MAX_CONCURRENT_CALLS", 1));
var languageEndpoint = builder.Configuration["LANGUAGE_ENDPOINT"];

if (!string.IsNullOrEmpty(builder.Configuration["APPLICATIONINSIGHTS_CONNECTION_STRING"]))
{
    builder.Services.AddOpenTelemetry().UseAzureMonitor();
}

// El worker tiene dos identidades asignadas (apps y scaler): AZURE_CLIENT_ID indica
// que el código use la de apps, que tiene permiso para recibir mensajes.
var credential = new DefaultAzureCredential();
builder.Services.AddSingleton(new ServiceBusClient(serviceBusFqdn, credential));
builder.Services.AddSingleton(options);

// Con LANGUAGE_ENDPOINT se usa Azure AI Language; sin él, el análisis simulado (sin costo ni cuota).
if (!string.IsNullOrEmpty(languageEndpoint))
{
    var languageOptions = new TextAnalyticsClientOptions();
    // El tier gratis (F0) limita las llamadas por minuto: más reintentos y más espera ante un 429.
    languageOptions.Retry.Mode = RetryMode.Exponential;
    languageOptions.Retry.MaxRetries = 6;
    languageOptions.Retry.MaxDelay = TimeSpan.FromSeconds(30);

    builder.Services.AddSingleton<ITextAnalyzer>(new LanguageTextAnalyzer(
        new TextAnalyticsClient(new Uri(languageEndpoint), credential, languageOptions)));
}
else
{
    builder.Services.AddSingleton<ITextAnalyzer>(
        new SimulatedTextAnalyzer(builder.Configuration.GetValue("PROCESSING_DELAY_MS", 2000)));
}

// Dentro del entorno de Container Apps, otra app se alcanza por su nombre: http://api
builder.Services.AddHttpClient("api", client =>
    client.BaseAddress = new Uri(builder.Configuration["API_BASE_URL"] ?? "http://api"));

builder.Services.AddSingleton<JobProcessor>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<JobProcessor>());

builder.Services.AddHealthChecks()
    .AddCheck<ProcessorHealthCheck>("processor", tags: ["ready"]);

var app = builder.Build();

app.MapGet("/", () => new
{
    service = "worker",
    revision = Environment.GetEnvironmentVariable("CONTAINER_APP_REVISION") ?? "local",
    replica = Environment.MachineName
});

app.MapHealthChecks("/health/live", new HealthCheckOptions { Predicate = _ => false });
app.MapHealthChecks("/health/ready", new HealthCheckOptions { Predicate = check => check.Tags.Contains("ready") });

app.Run();

static string Required(IConfiguration configuration, string key) =>
    configuration[key] is { Length: > 0 } value
        ? value
        : throw new InvalidOperationException($"Falta la variable de entorno obligatoria '{key}'.");

/// <summary>Readiness: el worker está listo cuando el procesador de Service Bus está escuchando.</summary>
internal class ProcessorHealthCheck(JobProcessor processor) : IHealthCheck
{
    public Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken cancellationToken = default) =>
        Task.FromResult(processor.IsProcessing
            ? HealthCheckResult.Healthy()
            : HealthCheckResult.Unhealthy("El procesador de Service Bus no está escuchando."));
}
