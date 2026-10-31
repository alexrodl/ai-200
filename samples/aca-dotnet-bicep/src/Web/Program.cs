using System.Text.Json;
using Azure.Monitor.OpenTelemetry.AspNetCore;
using Web;

var builder = WebApplication.CreateBuilder(args);

if (!string.IsNullOrEmpty(builder.Configuration["APPLICATIONINSIGHTS_CONNECTION_STRING"]))
{
    builder.Services.AddOpenTelemetry().UseAzureMonitor();
}

builder.Services.AddRazorPages();
builder.Services.AddHealthChecks();
builder.Services.AddSingleton(AppInfo.FromConfiguration(builder.Configuration));

// La API tiene ingress interno: solo se alcanza desde dentro del entorno, por su nombre.
builder.Services.AddHttpClient("api", client =>
    client.BaseAddress = new Uri(builder.Configuration["API_BASE_URL"] ?? "http://api"));

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
}

// Sin UseHttpsRedirection: Container Apps termina TLS en el ingress y el contenedor escucha HTTP en 8080.
app.UseRouting();
app.MapStaticAssets();
app.MapRazorPages().WithStaticAssets();

// Proxy hacia la API interna. La página llama a estos endpoints con fetch (wwwroot/js/site.js),
// así la web no guarda estado entre requests y cualquier réplica o revisión puede atender a cualquier usuario.
app.MapGet("/api/jobs", (IHttpClientFactory factory) =>
    Forward(() => factory.CreateClient("api").GetAsync("/jobs?take=25")));

app.MapPost("/api/jobs", (JsonElement body, IHttpClientFactory factory) =>
    Forward(() => factory.CreateClient("api").PostAsJsonAsync("/jobs", body)));

app.MapPost("/api/jobs/bulk", (JsonElement body, IHttpClientFactory factory) =>
    Forward(() => factory.CreateClient("api").PostAsJsonAsync("/jobs/bulk", body)));

// Endpoint para la prueba de carga HTTP (scripts/load-test.ps1): simula trabajo y
// devuelve qué versión, revisión y réplica respondió.
app.MapGet("/simulate", async (int? delayMs, AppInfo info) =>
{
    await Task.Delay(Math.Clamp(delayMs ?? 200, 0, 10_000));
    return info;
});

app.MapHealthChecks("/health/live");
app.MapHealthChecks("/health/ready");

app.Run();

static async Task<IResult> Forward(Func<Task<HttpResponseMessage>> call)
{
    try
    {
        using var response = await call();
        var body = await response.Content.ReadAsStringAsync();
        return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
    }
    catch (HttpRequestException ex)
    {
        return Results.Json(new { error = $"No se pudo contactar la API: {ex.Message}" }, statusCode: StatusCodes.Status502BadGateway);
    }
}
