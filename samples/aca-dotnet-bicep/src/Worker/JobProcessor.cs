using System.Diagnostics;
using System.Net;
using Azure.Messaging.ServiceBus;

namespace Worker;

public record JobMessage(Guid JobId, string Text);

public record JobResult(string Summary, string Sentiment, int WordCount, string Engine, string ProcessedBy, int DurationMs);

public record ProcessingOptions(string QueueName, int MaxConcurrentCalls);

/// <summary>
/// Lee mensajes de la cola de Service Bus, analiza el texto y devuelve el resultado a la API.
/// KEDA agrega o quita réplicas de este worker según los mensajes pendientes en la cola
/// (ver la regla 'servicebus-queue' en infra/apps.bicep).
/// </summary>
public sealed class JobProcessor : IHostedService, IAsyncDisposable
{
    private readonly ServiceBusProcessor _processor;
    private readonly ITextAnalyzer _analyzer;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ProcessingOptions _options;
    private readonly ILogger<JobProcessor> _logger;

    public JobProcessor(ServiceBusClient client, ITextAnalyzer analyzer, IHttpClientFactory httpClientFactory, ProcessingOptions options, ILogger<JobProcessor> logger)
    {
        _analyzer = analyzer;
        _httpClientFactory = httpClientFactory;
        _options = options;
        _logger = logger;

        // MaxConcurrentCalls bajo hace que cada réplica procese pocos mensajes a la vez,
        // así el escalado horizontal (más réplicas) se nota claramente en la demo.
        _processor = client.CreateProcessor(options.QueueName, new ServiceBusProcessorOptions
        {
            MaxConcurrentCalls = options.MaxConcurrentCalls,
            AutoCompleteMessages = true
        });
        _processor.ProcessMessageAsync += HandleMessageAsync;
        _processor.ProcessErrorAsync += HandleErrorAsync;
    }

    public bool IsProcessing => _processor.IsProcessing;

    public Task StartAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Worker {Replica} escuchando la cola '{Queue}' con el motor '{Engine}'",
            Environment.MachineName, _options.QueueName, _analyzer.Engine);
        return _processor.StartProcessingAsync(cancellationToken);
    }

    // Container Apps envía SIGTERM al reducir réplicas: se dejan de tomar mensajes nuevos
    // y se terminan los que están en curso.
    public Task StopAsync(CancellationToken cancellationToken) => _processor.StopProcessingAsync(cancellationToken);

    public ValueTask DisposeAsync() => _processor.DisposeAsync();

    private async Task HandleMessageAsync(ProcessMessageEventArgs args)
    {
        var message = args.Message.Body.ToObjectFromJson<JobMessage>()
            ?? throw new InvalidOperationException("Mensaje vacío.");
        var stopwatch = Stopwatch.StartNew();

        // Si Azure AI Language devuelve un error (por ejemplo, 429 por límite de llamadas del tier gratis),
        // el SDK reintenta; si sigue fallando, la excepción devuelve el mensaje a la cola para otro intento.
        var analysis = await _analyzer.AnalyzeAsync(message.Text, args.CancellationToken);

        var result = new JobResult(
            analysis.Summary,
            analysis.Sentiment,
            message.Text.Split(' ', StringSplitOptions.RemoveEmptyEntries).Length,
            _analyzer.Engine,
            Environment.MachineName,
            (int)stopwatch.ElapsedMilliseconds);

        var http = _httpClientFactory.CreateClient("api");
        var response = await http.PutAsJsonAsync($"/jobs/{message.JobId}/result", result, args.CancellationToken);

        if (response.StatusCode == HttpStatusCode.NotFound)
        {
            // El documento ya no existe en Cosmos DB (por ejemplo, expiró por TTL). No tiene sentido reintentar.
            _logger.LogWarning("La API no encontró el trabajo {JobId}. Se descarta el mensaje.", message.JobId);
            return;
        }

        // Cualquier otro error lanza una excepción: el mensaje vuelve a la cola y se reintenta.
        response.EnsureSuccessStatusCode();
        _logger.LogInformation("Trabajo {JobId} procesado en {DurationMs} ms con {Engine}: {Sentiment}",
            message.JobId, result.DurationMs, result.Engine, result.Sentiment);
    }

    private Task HandleErrorAsync(ProcessErrorEventArgs args)
    {
        _logger.LogError(args.Exception, "Error procesando mensajes ({Source})", args.ErrorSource);
        return Task.CompletedTask;
    }
}
