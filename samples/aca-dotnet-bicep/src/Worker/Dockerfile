# Etapa 1: compilar y publicar con el SDK de .NET 10.
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY Worker.csproj .
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /app --no-restore

# Etapa 2: imagen final solo con el runtime de ASP.NET Core (más chica y con menos superficie de ataque).
FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /app .
# Las imágenes de .NET escuchan en 8080 y traen un usuario sin privilegios (APP_UID).
EXPOSE 8080
USER $APP_UID
ENTRYPOINT ["dotnet", "Worker.dll"]
