// =============================================================================
// Infraestructura compartida: todo lo que las apps necesitan ANTES de existir.
//   - Log Analytics + Application Insights (observabilidad)
//   - Azure Container Registry (imágenes)
//   - Service Bus con la cola "jobs" (comunicación asíncrona api -> worker)
//   - Cosmos DB (los trabajos se guardan fuera de los contenedores)
//   - Azure AI Language (sentimiento y resumen con IA)
//   - Dos identidades administradas asignadas por el usuario + sus roles (RBAC)
//   - Entorno de Container Apps (límite compartido de red y logs)
//
// Se despliega primero y por separado porque las container apps referencian
// imágenes que todavía no existen: el script compila las imágenes en ACR entre
// este paso y apps.bicep.
// =============================================================================

@description('Región de los recursos.')
param location string = resourceGroup().location

@description('Sufijo único para los nombres globales (ACR, Service Bus).')
@minLength(5)
@maxLength(13)
param suffix string = uniqueString(resourceGroup().id)

@description('Nombre de la cola de Service Bus.')
param queueName string = 'jobs'

@description('Usar el free tier de Cosmos DB (1000 RU/s + 25 GB gratis). Solo se permite una cuenta free tier por suscripción; con false se crea como serverless.')
param cosmosFreeTier bool = true

@description('SKU de Azure AI Language. F0 es gratis (5.000 registros/mes) y se permite uno por suscripción.')
@allowed([
  'F0'
  'S'
])
param languageSku string = 'F0'

// IDs de roles integrados de Azure: https://learn.microsoft.com/azure/role-based-access-control/built-in-roles
var roles = {
  acrPull: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
  serviceBusDataSender: '69a216fc-b8fb-44d8-bc22-1f3c2cd27a39'
  serviceBusDataReceiver: '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0'
  serviceBusDataOwner: '090c5cfd-751d-490a-894a-3ce6f1109419'
  languageReader: '7628b7b8-a8b2-4cdc-b46f-e9b35248918e'
}

// Los roles de datos de Cosmos DB son propios de la cuenta (no son roles de Azure RBAC).
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

// ---------------------------------------------------------------------------
// Observabilidad
// ---------------------------------------------------------------------------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${suffix}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-${suffix}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// ---------------------------------------------------------------------------
// Registro de contenedores
// ---------------------------------------------------------------------------

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'acr${suffix}'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    // Sin usuario admin: las apps extraen las imágenes con identidad administrada (AcrPull).
    adminUserEnabled: false
  }
}

// ---------------------------------------------------------------------------
// Mensajería
// ---------------------------------------------------------------------------

resource serviceBus 'Microsoft.ServiceBus/namespaces@2024-01-01' = {
  name: 'sb-${suffix}'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    // Desactiva las claves SAS: solo se puede acceder con Microsoft Entra ID (identidades).
    disableLocalAuth: true
  }
}

resource queue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  parent: serviceBus
  name: queueName
  properties: {
    lockDuration: 'PT1M'
    // Tras 5 intentos fallidos, el mensaje pasa a la dead-letter queue.
    maxDeliveryCount: 5
  }
}

// ---------------------------------------------------------------------------
// Datos: Cosmos DB guarda los trabajos fuera de los contenedores
// ---------------------------------------------------------------------------

resource cosmos 'Microsoft.DocumentDB/databaseAccounts@2024-11-15' = {
  name: 'cosmos-${suffix}'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: cosmosFreeTier
    // Sin claves: solo identidades de Microsoft Entra ID con un rol de datos.
    disableLocalAuth: true
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
    // El free tier usa throughput aprovisionado; si no está disponible, se usa serverless (pago por uso).
    capabilities: cosmosFreeTier ? [] : [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-11-15' = {
  parent: cosmos
  name: 'jobsdb'
  properties: {
    resource: {
      id: 'jobsdb'
    }
    // 1000 RU/s compartidas por la base: es exactamente lo que cubre el free tier.
    options: cosmosFreeTier ? { throughput: 1000 } : {}
  }
}

resource cosmosContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-11-15' = {
  parent: cosmosDatabase
  name: 'jobs'
  properties: {
    resource: {
      id: 'jobs'
      partitionKey: {
        paths: [
          '/id'
        ]
        kind: 'Hash'
      }
      // Los trabajos se borran solos a los 7 días: la demo no acumula datos.
      defaultTtl: 604800
    }
  }
}

// ---------------------------------------------------------------------------
// IA: Azure AI Language (Foundry Tools) para sentimiento y resumen
// ---------------------------------------------------------------------------

resource language 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: 'lang-${suffix}'
  location: location
  kind: 'TextAnalytics'
  sku: {
    name: languageSku
  }
  properties: {
    // El subdominio propio es obligatorio para autenticarse con Microsoft Entra ID.
    customSubDomainName: 'lang-${suffix}'
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}

// ---------------------------------------------------------------------------
// Identidades y permisos
// ---------------------------------------------------------------------------

// Identidad que usan las apps: extraer imágenes, enviar/recibir mensajes,
// leer/escribir en Cosmos DB y llamar a Azure AI Language.
resource appsIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-apps-${suffix}'
  location: location
}

// Identidad que usa KEDA para leer cuántos mensajes hay en la cola.
// Leer las propiedades de la cola requiere el rol Data Owner, por eso se separa
// de la identidad de las apps (mínimo privilegio para el código).
resource scalerIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-scaler-${suffix}'
  location: location
}

resource acrPullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, appsIdentity.id, roles.acrPull)
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.acrPull)
    principalId: appsIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource senderAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBus.id, appsIdentity.id, roles.serviceBusDataSender)
  scope: serviceBus
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.serviceBusDataSender)
    principalId: appsIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource receiverAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBus.id, appsIdentity.id, roles.serviceBusDataReceiver)
  scope: serviceBus
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.serviceBusDataReceiver)
    principalId: appsIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource scalerAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBus.id, scalerIdentity.id, roles.serviceBusDataOwner)
  scope: serviceBus
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.serviceBusDataOwner)
    principalId: scalerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource languageAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(language.id, appsIdentity.id, roles.languageReader)
  scope: language
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.languageReader)
    principalId: appsIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource cosmosDataAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-11-15' = {
  parent: cosmos
  name: guid(cosmos.id, appsIdentity.id, cosmosDataContributorRoleId)
  properties: {
    roleDefinitionId: '${cosmos.id}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'
    principalId: appsIdentity.properties.principalId
    scope: cosmos.id
  }
}

// ---------------------------------------------------------------------------
// Entorno de Container Apps
// ---------------------------------------------------------------------------

resource environment 'Microsoft.App/managedEnvironments@2025-01-01' = {
  name: 'cae-${suffix}'
  location: location
  properties: {
    // Los logs de consola y de sistema de todas las apps van a Log Analytics.
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

output environmentName string = environment.name
output registryName string = registry.name
output registryLoginServer string = registry.properties.loginServer
output serviceBusName string = serviceBus.name
output queueName string = queue.name
output appsIdentityName string = appsIdentity.name
output scalerIdentityName string = scalerIdentity.name
output appInsightsName string = appInsights.name
output cosmosAccountName string = cosmos.name
output cosmosDatabaseName string = cosmosDatabase.name
output cosmosContainerName string = cosmosContainer.name
output languageAccountName string = language.name
output logAnalyticsWorkspaceId string = logAnalytics.properties.customerId
