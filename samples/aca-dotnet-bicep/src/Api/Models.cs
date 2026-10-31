namespace Api;

public enum JobStatus
{
    Pending,
    Completed
}

/// <summary>Un trabajo de análisis de texto. Se guarda como documento en Cosmos DB (ver JobStore).</summary>
public record Job(
    Guid Id,
    string Text,
    JobStatus Status,
    DateTimeOffset CreatedAt,
    DateTimeOffset? CompletedAt,
    JobResult? Result);

/// <summary>Resultado que el worker envía cuando termina de procesar un trabajo.</summary>
public record JobResult(
    string Summary,
    string Sentiment,
    int WordCount,
    string Engine,
    string ProcessedBy,
    int DurationMs);

/// <summary>Mensaje que viaja por la cola de Service Bus hacia el worker.</summary>
public record JobMessage(Guid JobId, string Text);

public record CreateJobRequest(string Text);

public record BulkJobsRequest(int Count);

public record JobStats(int Total, int Pending, int Completed, int WorkerReplicas);

public record JobsSnapshot(string ApiReplica, JobStats Stats, IReadOnlyList<Job> Jobs);
