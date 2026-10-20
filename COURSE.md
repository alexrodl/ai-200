# Guía de entrega - AI-200T00-A

## Datos del curso

- **Nombre oficial:** Develop AI cloud solutions on Azure
- **Código:** AI-200T00-A
- **Duración de esta entrega:** diez días; una clase diaria de tres horas, incluido un corte de 15 minutos (2 h 45 min netos de clase).
- **Nivel / rol:** intermedio / desarrollador
- **Programa oficial:** [Microsoft Learn - AI-200T00](https://learn.microsoft.com/en-us/training/courses/ai-200t00)
- **Audiencia:** desarrolladores de aplicaciones backend y soluciones con IA en Azure.

El propósito es que los participantes desarrollen, desplieguen, integren, aseguren, observen y diagnostiquen aplicaciones de IA en Azure. El contenido técnico sigue los nueve learning paths enlazados desde el curso oficial.

## Plan de diez días

Cada clase dura tres horas e incluye un corte de 15 minutos; quedan 2 h 45 min netos para explicación, demostraciones, práctica y validación. La distribución de cada sesión puede ajustarse al ritmo de la cohorte. Los tiempos estimados de los ejercicios Microsoft se indican en sus materiales.

| Día | Módulo | Énfasis |
|---|---|---|
| 1 | 1 | Container application hosting: contenedores, registro y opciones de alojamiento |
| 2 | 2 | Azure Container Apps: despliegues, revisiones y escalado |
| 3 | 3 | Azure Kubernetes Service: arquitectura y despliegue |
| 4 | 3 | Azure Kubernetes Service: operación, diagnóstico y práctica |
| 5 | 4 | Azure Cosmos DB for NoSQL: persistencia, consultas y búsqueda vectorial |
| 6 | 5 | Azure Database for PostgreSQL: PostgreSQL, pgvector y búsqueda vectorial |
| 7 | 6 | Azure Managed Redis: caché, mensajería y vectores |
| 8 | 7 | Backend services: integración y flujos por eventos |
| 9 | 8 | Secrets and configuration: Key Vault e integración de configuración |
| 10 | 9 y cierre | Observabilidad, troubleshooting, integración de aprendizajes y limpieza de recursos |

## Objetivos de aprendizaje

Al terminar, los participantes podrán aplicar patrones del curso para:

- Crear y administrar imágenes de contenedor y alojar aplicaciones en Azure.
- Desplegar aplicaciones en Azure Container Apps y AKS, configurar ejecución, escalado y diagnóstico.
- Diseñar persistencia para aplicaciones de IA con Cosmos DB for NoSQL, PostgreSQL/pgvector y Managed Redis.
- Integrar backends mediante Service Bus, Event Grid y Azure Functions.
- Gestionar secretos y configuración con Key Vault, identidades administradas y App Configuration.
- Instrumentar aplicaciones y analizar telemetría con OpenTelemetry, Azure Monitor y KQL.

## Secuencia oficial y guías locales

1. [Container application hosting](modules/01-container-app-hosting/README.md) · [Lab 1](labs/lab-01-container-app-hosting/README.md)
2. [Azure Container Apps](modules/02-azure-container-apps/README.md) · [Lab 2](labs/lab-02-azure-container-apps/README.md)
3. [Azure Kubernetes Service](modules/03-azure-kubernetes-service/README.md) · [Lab 3](labs/lab-03-azure-kubernetes-service/README.md)
4. [Azure Cosmos DB for NoSQL](modules/04-azure-cosmos-db/README.md) · [Lab 4](labs/lab-04-azure-cosmos-db/README.md)
5. [Azure Database for PostgreSQL](modules/05-azure-database-postgresql/README.md) · [Lab 5](labs/lab-05-azure-database-postgresql/README.md)
6. [Azure Managed Redis](modules/06-azure-managed-redis/README.md) · [Lab 6](labs/lab-06-azure-managed-redis/README.md)
7. [Backend services](modules/07-backend-services/README.md) · [Lab 7](labs/lab-07-backend-services/README.md)
8. [Secrets and configuration](modules/08-secrets-and-configuration/README.md) · [Lab 8](labs/lab-08-secrets-and-configuration/README.md)
9. [Observability and troubleshooting](modules/09-observability-and-troubleshooting/README.md) · [Lab 9](labs/lab-09-observability-and-troubleshooting/README.md)

Cada módulo agrupa los ejercicios prácticos referenciados en el material de entrenador en español. Las guías locales indican objetivos, preparación y comprobaciones; el ejercicio Microsoft enlazado contiene el procedimiento oficial.

## Requisitos previos sugeridos

- Experiencia de programación, especialmente Python; algunos escenarios admiten JavaScript o C#.
- Conceptos básicos de Azure, cloud computing, APIs y línea de comandos.
- Familiaridad con contenedores; Kubernetes para el módulo de AKS.
- SQL/JSON y conceptos de embeddings/vector search para los módulos de datos.
- Suscripción y cuota autorizadas para crear recursos. Consulta [prerrequisitos](prerequisites/README.md).

## Práctica docente

- Explicar el escenario y el patrón antes de empezar cada ejercicio.
- Pedir a los alumnos que anoten decisiones, salidas de validación y problemas encontrados, sin incluir secretos.
- Comparar opciones de hosting y persistencia, no solo completar comandos.
- No prometer que una arquitectura o servicio del curso sea universalmente preferible.
- Al cerrar cada práctica, comprobar la limpieza de los recursos de Azure.

## Material público y restricciones

El repositorio debe contener solo material que pueda compartirse públicamente. No incluir preguntas reales del examen, dumps, credenciales, datos personales ni notas confidenciales de instructor. Distinguir con claridad la documentación oficial de la explicación y guía complementaria del instructor.
