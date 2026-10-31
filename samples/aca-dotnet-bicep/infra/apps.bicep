// =============================================================================
// Las tres container apps del ejemplo:
//
//   web    -> ingress EXTERNO, escala por HTTP, modo de revisiones MÚLTIPLES
//   api    -> ingress INTERNO, escala por HTTP, guarda los trabajos en Cosmos DB
//   worker -> SIN ingress, escala de 0 a N con KEDA según la cola de Service Bus,
//             analiza los textos con Azure AI Language
//
// Requiere que core.bicep ya esté desplegado y que las imágenes existan en ACR.
// =============================================================================

param location string = resourceGroup().location
param environmentName string
param registryLoginServer string
param serviceBusName string
param queueName string
param appsIdentityName string
param scalerIdentityName string
param appInsightsName string
param cosmosAccountName string
param cosmosDatabaseName string
param cosmosContainerName string
param languageAccountName string

@description('Etiqueta de las imágenes compiladas por el script (por ejemplo, 20261028153000).')
param imageTag string

@description('Versión que muestra la web. Cambiarla ayuda a ver la división de tráfico entre revisiones.')
param webVersion string = 'v1'

resource environment 'Microsoft.App/managedEnvironments@2025-01-01' existing = {
  name: environmentName
}

resource appsIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: appsIdentityName
}

resource scalerIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: scalerIdentityName
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' existing = {
  name: cosmosAccountName
}

resource language 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: languageAccountName
}

// Configuración común a las tres apps -----------------------------------------

// Extraer imágenes de ACR con la identidad administrada (rol AcrPull), sin contraseñas.
var registries = [
  {
    server: registryLoginServer
    identity: appsIdentity.id
  }
]

// La connection string de Application Insights se guarda como SECRETO de la app
// y se expone al contenedor con secretRef, no como valor en texto plano.
var secrets = [
  {
    name: 'appinsights-connection-string'
    value: appInsights.properties.ConnectionString
  }
]

var commonEnv = [
  {
    name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
    secretRef: 'appinsights-connection-string'
  }
  {
    // Activa las trazas del SDK de Service Bus (todavía experimentales) para ver
    // el recorrido completo web -> api -> cola -> worker en Application Insights.
    name: 'AZURE_EXPERIMENTAL_ENABLE_ACTIVITY_SOURCE'
    value: 'true'
  }
  {
    // Indica a DefaultAzureCredential qué identidad administrada usar.
    name: 'AZURE_CLIENT_ID'
    value: appsIdentity.properties.clientId
  }
]

var serviceBusEnv = [
  {
    name: 'SERVICEBUS_FQDN'
    value: '${serviceBusName}.servicebus.windows.net'
  }
  {
    name: 'SERVICEBUS_QUEUE'
    value: queueName
  }
]

// Sondeos: liveness reinicia el contenedor si deja de responder;
// readiness lo saca del balanceo mientras no esté listo.
var probes = [
  {
    type: 'Liveness'
    httpGet: {
      path: '/health/live'
      port: 8080
    }
    initialDelaySeconds: 5
    periodSeconds: 10
  }
  {
    type: 'Readiness'
    httpGet: {
      path: '/health/ready'
      port: 8080
    }
    initialDelaySeconds: 3
    periodSeconds: 5
  }
]

var resources = {
  cpu: json('0.25')
  memory: '0.5Gi'
}

// -----------------------------------------------------------------------------
// api: ingress interno, accesible solo dentro del entorno como http://api
// -----------------------------------------------------------------------------

resource api 'Microsoft.App/containerApps@2025-01-01' = {
  name: 'api'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${appsIdentity.id}': {}
    }
  }
  properties: {
    environmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false
        targetPort: 8080
        // Permite llamadas HTTP (sin TLS) desde las otras apps del entorno: http://api
        allowInsecure: true
      }
      registries: registries
      secrets: secrets
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${registryLoginServer}/api:${imageTag}'
          resources: resources
          env: concat(commonEnv, serviceBusEnv, [
            {
              name: 'OTEL_SERVICE_NAME'
              value: 'api'
            }
            {
              name: 'COSMOS_ENDPOINT'
              value: cosmos.properties.documentEndpoint
            }
            {
              name: 'COSMOS_DATABASE'
              value: cosmosDatabaseName
            }
            {
              name: 'COSMOS_CONTAINER'
              value: cosmosContainerName
            }
          ])
          probes: probes
        }
      ]
      scale: {
        // El estado vive en Cosmos DB, no en la réplica: la API puede escalar sin perder datos.
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-concurrency'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
}

// -----------------------------------------------------------------------------
// worker: sin ingress, escala con KEDA según los mensajes pendientes en la cola
// -----------------------------------------------------------------------------

resource worker 'Microsoft.App/containerApps@2025-01-01' = {
  name: 'worker'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${appsIdentity.id}': {}
      '${scalerIdentity.id}': {}
    }
  }
  properties: {
    environmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      registries: registries
      secrets: secrets
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: '${registryLoginServer}/worker:${imageTag}'
          resources: resources
          env: concat(commonEnv, serviceBusEnv, [
            {
              name: 'OTEL_SERVICE_NAME'
              value: 'worker'
            }
            {
              name: 'API_BASE_URL'
              value: 'http://api'
            }
            {
              // Endpoint de Azure AI Language. Si se quita esta variable, el worker usa el análisis simulado.
              name: 'LANGUAGE_ENDPOINT'
              value: language.properties.endpoint
            }
            {
              // Mensajes en paralelo por réplica. Bajo = el escalado horizontal se nota más.
              name: 'MAX_CONCURRENT_CALLS'
              value: '1'
            }
          ])
          // Los sondeos funcionan aunque la app no tenga ingress: Container Apps
          // llama directamente al puerto del contenedor.
          probes: probes
        }
      ]
      scale: {
        // Escala a cero cuando la cola está vacía: no se paga cómputo sin trabajo.
        minReplicas: 0
        maxReplicas: 10
        // Valores más bajos que los por defecto (30 s y 300 s) para que la demo se vea en clase.
        pollingInterval: 15
        cooldownPeriod: 60
        rules: [
          {
            name: 'servicebus-queue'
            custom: {
              // Scaler de KEDA: https://keda.sh/docs/latest/scalers/azure-service-bus/
              type: 'azure-servicebus'
              // KEDA se autentica con la identidad "scaler" (rol Data Owner), sin connection string.
              identity: scalerIdentity.id
              metadata: {
                namespace: serviceBusName
                queueName: queueName
                // Objetivo: ~5 mensajes pendientes por réplica.
                messageCount: '5'
              }
            }
          }
        ]
      }
    }
  }
}

// -----------------------------------------------------------------------------
// web: ingress externo, escala por HTTP, modo de revisiones múltiples
// -----------------------------------------------------------------------------

resource web 'Microsoft.App/containerApps@2025-01-01' = {
  name: 'web'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${appsIdentity.id}': {}
    }
  }
  properties: {
    environmentId: environment.id
    configuration: {
      // Varias revisiones activas a la vez para repartir el tráfico (ver scripts/traffic-split.ps1).
      activeRevisionsMode: 'Multiple'
      ingress: {
        external: true
        targetPort: 8080
        // Al volver a desplegar esta plantilla, el 100 % del tráfico vuelve a la última revisión.
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: registries
      secrets: secrets
    }
    template: {
      containers: [
        {
          name: 'web'
          image: '${registryLoginServer}/web:${imageTag}'
          resources: resources
          env: concat(commonEnv, [
            {
              name: 'OTEL_SERVICE_NAME'
              value: 'web'
            }
            {
              name: 'API_BASE_URL'
              value: 'http://api'
            }
            {
              name: 'APP_VERSION'
              value: webVersion
            }
          ])
          probes: probes
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-concurrency'
            http: {
              metadata: {
                // Una réplica nueva por cada ~10 solicitudes simultáneas.
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
  // La web llama a la API: se crea después para que la primera revisión ya la encuentre.
  dependsOn: [
    api
  ]
}

output webUrl string = 'https://${web.properties.configuration.ingress.fqdn}'
