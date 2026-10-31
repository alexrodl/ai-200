using System.Text.Json;
using System.Text.Json.Serialization;
using Api;
using Azure.Identity;
using Azure.Messaging.ServiceBus;
using Azure.Monitor.OpenTelemetry.AspNetCore;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.Azure.Cosmos;

var builder = WebApplication.CreateBuilder(args);

// La configuración llega como variables de entorno definidas en infra/apps.bicep.
// Si falta una obligatoria, la app falla al arrancar con un mensaje claro en los logs:
// así se puede practicar el diagnóstico de una revisión que no inicia.
var serviceBusFqdn = Required(builder.Configuration, "SERVICEBUS_FQDN");
var queueName = builder.Configuration["SERVICEBUS_QUEUE"] ?? "jobs";
var cosmosEndpoint = Required(builder.Configuration, "COSMOS_ENDPOINT");
var cosmosDatabase = builder.Configuration["COSMOS_DATABASE"] ?? "jobsdb";
var cosmosContainer = builder.Configuration["COSMOS_CONTAINER"] ?? "jobs";

// Application Insights (OpenTelemetry). La connection string llega como secreto de Container Apps.
if (!string.IsNullOrEmpty(builder.Configuration["APPLICATIONINSIGHTS_CONNECTION_STRING"]))
{
    builder.Services.AddOpenTelemetry().UseAzureMonitor();
}

// DefaultAzureCredential usa la identidad administrada en Azure (AZURE_CLIENT_ID indica cuál)
// y tu sesión de 'az login' cuando corres en local. No hay connection strings ni claves.
var credential = new DefaultAzureCredential();
builder.Services.AddSingleton(new ServiceBusClient(serviceBusFqdn, credential));
builder.Services.AddSingleton(sp => sp.GetRequiredService<ServiceBusClient>().CreateSender(queueName));

// Cosmos DB también con identidad administrada (rol de datos "Built-in Data Contributor").
var cosmosClient = new CosmosClient(cosmosEndpoint, credential, new CosmosClientOptions
{
    UseSystemTextJsonSerializerWithOptions = new JsonSerializerOptions(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() }
    }
});
builder.Services.AddSingleton(cosmosClient.GetContainer(cosmosDatabase, cosmosContainer));
builder.Services.AddSingleton<JobStore>();

builder.Services.AddHealthChecks()
    .AddCheck<ServiceBusHealthCheck>("servicebus", tags: ["ready"]);

builder.Services.ConfigureHttpJsonOptions(options =>
    options.SerializerOptions.Converters.Add(new JsonStringEnumConverter()));

var app = builder.Build();

app.MapGet("/", () => new
{
    service = "api",
    revision = Environment.GetEnvironmentVariable("CONTAINER_APP_REVISION") ?? "local",
    replica = Environment.MachineName
});

// Crea un trabajo y lo encola. Devuelve 202: el procesamiento ocurre después, en el worker.
app.MapPost("/jobs", async (CreateJobRequest request, JobStore store, ServiceBusSender sender) =>
{
    if (string.IsNullOrWhiteSpace(request.Text))
    {
        return Results.BadRequest(new { error = "El texto es obligatorio." });
    }

    var job = await store.CreateAsync(request.Text.Trim());
    await sender.SendMessageAsync(ToMessage(job));
    return Results.Accepted($"/jobs/{job.Id}", job);
});

// Genera muchos trabajos de una vez para llenar la cola y ver escalar al worker con KEDA.
// Máximo 200: cada trabajo consume registros de la cuota gratis de Azure AI Language.
app.MapPost("/jobs/bulk", async (BulkJobsRequest request, JobStore store, ServiceBusSender sender) =>
{
    var count = Math.Clamp(request.Count, 1, 200);
    var jobs = await Task.WhenAll(Enumerable.Range(0, count).Select(i => store.CreateAsync(SampleTexts.Pick(i))));
    var pending = new Queue<ServiceBusMessage>(jobs.Select(ToMessage));

    // Envía los mensajes en lotes en lugar de una llamada por mensaje.
    while (pending.Count > 0)
    {
        using var batch = await sender.CreateMessageBatchAsync();
        while (pending.Count > 0 && batch.TryAddMessage(pending.Peek()))
        {
            pending.Dequeue();
        }
        await sender.SendMessagesAsync(batch);
    }

    return Results.Accepted("/jobs", new { created = count });
});

app.MapGet("/jobs", (JobStore store, int? take) => store.SnapshotAsync(Math.Clamp(take ?? 50, 1, 500)));

// El worker llama a este endpoint por la red interna del entorno (http://api) al terminar.
app.MapPut("/jobs/{id:guid}/result", async (Guid id, JobResult result, JobStore store) =>
    await store.CompleteAsync(id, result) ? Results.NoContent() : Results.NotFound());

// Liveness: el proceso responde. Readiness: además, las dependencias están disponibles.
app.MapHealthChecks("/health/live", new HealthCheckOptions { Predicate = _ => false });
app.MapHealthChecks("/health/ready", new HealthCheckOptions { Predicate = check => check.Tags.Contains("ready") });

app.Run();

static ServiceBusMessage ToMessage(Job job) =>
    new(BinaryData.FromObjectAsJson(new JobMessage(job.Id, job.Text)))
    {
        MessageId = job.Id.ToString(),
        ContentType = "application/json"
    };

static string Required(IConfiguration configuration, string key) =>
    configuration[key] is { Length: > 0 } value
        ? value
        : throw new InvalidOperationException($"Falta la variable de entorno obligatoria '{key}'.");
