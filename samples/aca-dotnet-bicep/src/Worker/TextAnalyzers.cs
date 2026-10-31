using Azure;
using Azure.AI.TextAnalytics;

namespace Worker;

public record TextAnalysis(string Summary, string Sentiment);

public interface ITextAnalyzer
{
    string Engine { get; }

    Task<TextAnalysis> AnalyzeAsync(string text, CancellationToken cancellationToken);
}

/// <summary>
/// Análisis real con Azure AI Language (Foundry Tools): sentimiento y resumen abstractivo.
/// Se autentica con la identidad administrada (rol Cognitive Services Language Reader).
/// </summary>
public sealed class LanguageTextAnalyzer(TextAnalyticsClient client) : ITextAnalyzer
{
    private const string Language = "es";

    public string Engine => "Azure AI Language";

    public async Task<TextAnalysis> AnalyzeAsync(string text, CancellationToken cancellationToken)
    {
        // Las dos llamadas son independientes: se hacen en paralelo.
        var sentiment = AnalyzeSentimentAsync(text, cancellationToken);
        var summary = SummarizeAsync(text, cancellationToken);
        await Task.WhenAll(sentiment, summary);

        return new TextAnalysis(summary.Result, sentiment.Result);
    }

    private async Task<string> AnalyzeSentimentAsync(string text, CancellationToken cancellationToken)
    {
        DocumentSentiment result = await client.AnalyzeSentimentAsync(text, Language, cancellationToken: cancellationToken);
        return result.Sentiment switch
        {
            TextSentiment.Positive => "positivo",
            TextSentiment.Negative => "negativo",
            TextSentiment.Mixed => "mixto",
            _ => "neutral"
        };
    }

    // El resumen abstractivo es una operación asíncrona: se envía un job y se espera a que termine.
    private async Task<string> SummarizeAsync(string text, CancellationToken cancellationToken)
    {
        var operation = await client.AbstractiveSummarizeAsync(
            WaitUntil.Completed,
            [text],
            Language,
            new AbstractiveSummarizeOptions { SentenceCount = 1 },
            cancellationToken);

        await foreach (var page in operation.Value)
        {
            foreach (var document in page)
            {
                if (document.HasError)
                {
                    throw new InvalidOperationException($"Azure AI Language: {document.Error.ErrorCode} - {document.Error.Message}");
                }
                return document.Summaries.Count > 0 ? document.Summaries.First().Text : "";
            }
        }

        return "";
    }
}

/// <summary>
/// Análisis simulado (sin IA): se usa cuando no hay LANGUAGE_ENDPOINT configurado.
/// Imita la latencia de un modelo y clasifica contando palabras clave.
/// </summary>
public sealed class SimulatedTextAnalyzer(int delayMs) : ITextAnalyzer
{
    private static readonly string[] PositiveWords = ["excelente", "bueno", "buen", "rápido", "feliz", "recomiendo", "genial", "funciona", "mejor", "linda"];
    private static readonly string[] NegativeWords = ["malo", "mala", "lenta", "lento", "terrible", "error", "problema", "caro", "molestó", "escaso"];

    public string Engine => "simulado";

    public async Task<TextAnalysis> AnalyzeAsync(string text, CancellationToken cancellationToken)
    {
        await Task.Delay(delayMs, cancellationToken);

        var words = text.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        var normalized = words.Select(w => w.Trim('.', ',', ';', ':', '!', '?', '¡', '¿').ToLowerInvariant()).ToList();

        var score = normalized.Count(PositiveWords.Contains) - normalized.Count(NegativeWords.Contains);
        var sentiment = score switch
        {
            > 0 => "positivo",
            < 0 => "negativo",
            _ => "neutral"
        };

        var summary = words.Length <= 12 ? text : string.Join(' ', words.Take(12)) + "…";
        return new TextAnalysis(summary, sentiment);
    }
}
