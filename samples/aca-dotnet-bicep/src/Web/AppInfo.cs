namespace Web;

/// <summary>
/// Datos de la instancia que atiende la solicitud. Container Apps inyecta CONTAINER_APP_REVISION
/// automáticamente; el nombre de la máquina es el nombre de la réplica.
/// </summary>
public record AppInfo(string Version, string Revision, string Replica)
{
    public static AppInfo FromConfiguration(IConfiguration configuration) => new(
        Version: configuration["APP_VERSION"] ?? "v1",
        Revision: configuration["CONTAINER_APP_REVISION"] ?? "local",
        Replica: Environment.MachineName);
}
