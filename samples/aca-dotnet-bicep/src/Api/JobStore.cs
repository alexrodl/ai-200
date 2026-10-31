using System.Net;
using Microsoft.Azure.Cosmos;

namespace Api;

/// <summary>
/// Guarda los trabajos en Azure Cosmos DB (un documento por trabajo, partición por /id).
/// Como el estado vive fuera del contenedor, la API no tiene estado: puede reiniciarse
/// o escalar a varias réplicas sin perder trabajos.
/// </summary>
public class JobStore(Container container)
{
    public async Task<Job> CreateAsync(string text)
    {
        var job = new Job(Guid.NewGuid(), text, JobStatus.Pending, DateTimeOffset.UtcNow, null, null);
        await container.CreateItemAsync(job, new PartitionKey(job.Id.ToString()));
        return job;
    }

    public async Task<bool> CompleteAsync(Guid id, JobResult result)
    {
        try
        {
            // Patch actualiza solo estos campos sin leer y reescribir el documento completo.
            await container.PatchItemAsync<Job>(id.ToString(), new PartitionKey(id.ToString()),
            [
                PatchOperation.Set("/status", JobStatus.Completed),
                PatchOperation.Set("/completedAt", DateTimeOffset.UtcNow),
                PatchOperation.Set("/result", result)
            ]);
            return true;
        }
        catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.NotFound)
        {
            return false;
        }
    }

    public async Task<JobsSnapshot> SnapshotAsync(int take)
    {
        var latest = QueryAsync<Job>(new QueryDefinition("SELECT TOP @take * FROM c ORDER BY c.createdAt DESC")
            .WithParameter("@take", take));
        var pending = CountAsync(JobStatus.Pending);
        var completed = CountAsync(JobStatus.Completed);
        // Cuántas réplicas distintas del worker procesaron trabajos: se ve el escalado de KEDA.
        var workers = QueryAsync<string>(new QueryDefinition(
            "SELECT DISTINCT VALUE c.result.processedBy FROM c WHERE c.status = 'Completed'"));

        await Task.WhenAll(latest, pending, completed, workers);

        var stats = new JobStats(
            Total: pending.Result + completed.Result,
            Pending: pending.Result,
            Completed: completed.Result,
            WorkerReplicas: workers.Result.Count);
        return new JobsSnapshot(Environment.MachineName, stats, latest.Result);
    }

    private async Task<int> CountAsync(JobStatus status)
    {
        var counts = await QueryAsync<int>(new QueryDefinition("SELECT VALUE COUNT(1) FROM c WHERE c.status = @status")
            .WithParameter("@status", status.ToString()));
        return counts.Sum();
    }

    private async Task<List<T>> QueryAsync<T>(QueryDefinition query)
    {
        var results = new List<T>();
        using var iterator = container.GetItemQueryIterator<T>(query);
        while (iterator.HasMoreResults)
        {
            results.AddRange(await iterator.ReadNextAsync());
        }
        return results;
    }
}
