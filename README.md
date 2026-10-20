# AI-200T00-A: Develop AI Cloud Solutions on Azure

Portal de aprendizaje en español para el curso oficial de Microsoft. La secuencia sigue los **nueve learning paths** publicados en el [programa oficial de AI-200T00](https://learn.microsoft.com/en-us/training/courses/ai-200t00).

El curso se centra en desarrollar, desplegar, integrar, proteger, observar y solucionar problemas de aplicaciones con IA en Azure. No es un curso genérico de Azure AI Services ni una colección de preguntas del examen.

## Cómo usar este repositorio

1. Revisa los [prerrequisitos](prerequisites/README.md) y prepara el [entorno](docs/environment-setup.md).
2. Sigue los módulos en orden. Cada módulo enlaza al learning path oficial de Microsoft Learn.
3. Completa los ejercicios del módulo en el [portal oficial de laboratorios AI-200](https://microsoftlearning.github.io/mslearn-azure-ai/). Las guías locales agrupan esos ejercicios por módulo y aportan objetivos, verificación y notas de entrega en español.
4. Elimina los recursos temporales al terminar cada práctica.

## Programa del curso

La entrega se organiza en **10 días**, con una clase diaria de **3 horas** que incluye un corte de **15 minutos** (2 h 45 min netos de clase). El módulo de Azure Kubernetes Service se distribuye en dos días; el último día se dedica a observabilidad, troubleshooting y cierre.

| Día | Contenido |
|---|---|
| 1 | Container application hosting: Azure Container Registry (ACR) Tasks y contenedores en Azure App Service ([guía de clase](classes/class-01-container-hosting/README.md)) |
| 2 | Azure Container Apps |
| 3 | Azure Kubernetes Service: arquitectura y despliegue |
| 4 | Azure Kubernetes Service: operación, diagnóstico y práctica |
| 5 | Azure Cosmos DB for NoSQL |
| 6 | Azure Database for PostgreSQL |
| 7 | Azure Managed Redis |
| 8 | Backend services for AI |
| 9 | Secrets and configuration |
| 10 | Observability and troubleshooting; integración de aprendizajes y cierre |

| # | Módulo | Contenido | Guía del módulo | Laboratorio |
|---|---|---|---|---|
| 1 | Container application hosting | Azure Container Registry, Azure App Service y contenedores | [Módulo 1](modules/01-container-app-hosting/README.md) | [Lab 1](labs/lab-01-container-app-hosting/README.md) |
| 2 | Azure Container Apps | Despliegues, revisiones, diagnóstico y escalado | [Módulo 2](modules/02-azure-container-apps/README.md) | [Lab 2](labs/lab-02-azure-container-apps/README.md) |
| 3 | Azure Kubernetes Service | Despliegue, configuración, monitorización y troubleshooting | [Módulo 3](modules/03-azure-kubernetes-service/README.md) | [Lab 3](labs/lab-03-azure-kubernetes-service/README.md) |
| 4 | Azure Cosmos DB for NoSQL | Persistencia, consultas, vector search e índices | [Módulo 4](modules/04-azure-cosmos-db/README.md) | [Lab 4](labs/lab-04-azure-cosmos-db/README.md) |
| 5 | Azure Database for PostgreSQL | PostgreSQL, pgvector y búsqueda vectorial | [Módulo 5](modules/05-azure-database-postgresql/README.md) | [Lab 5](labs/lab-05-azure-database-postgresql/README.md) |
| 6 | Azure Managed Redis | Operaciones de datos, mensajería y vectores | [Módulo 6](modules/06-azure-managed-redis/README.md) | [Lab 6](labs/lab-06-azure-managed-redis/README.md) |
| 7 | Backend services for AI | Service Bus, Event Grid y Azure Functions | [Módulo 7](modules/07-backend-services/README.md) | [Lab 7](labs/lab-07-backend-services/README.md) |
| 8 | Secrets and configuration | Key Vault y App Configuration | [Módulo 8](modules/08-secrets-and-configuration/README.md) | [Lab 8](labs/lab-08-secrets-and-configuration/README.md) |
| 9 | Observability and troubleshooting | OpenTelemetry, Application Insights, logs y KQL | [Módulo 9](modules/09-observability-and-troubleshooting/README.md) | [Lab 9](labs/lab-09-observability-and-troubleshooting/README.md) |

## Estructura

- [modules/](modules/): objetivos, contenidos y vínculo Microsoft Learn de cada learning path.
- [classes/](classes/): agenda, resumen y ejercicios organizados por clase.
- [labs/](labs/): una guía práctica por cada uno de los nueve módulos.
- [prerequisites/](prerequisites/): conocimientos, suscripción, cuentas y herramientas.
- [docs/](docs/): preparación del entorno y recursos adicionales.
- [troubleshooting/](troubleshooting/README.md): diagnóstico inicial de incidencias.
- [Materiales/](Materiales/): presentaciones y material de entrenador existente; no publicar material restringido.

## Laboratorios y atribución

El [portal oficial de laboratorios AI-200](https://microsoftlearning.github.io/mslearn-azure-ai/) es la fuente de instrucciones prácticas. Cada guía local enlaza a las páginas específicas de cada ejercicio en dicho portal y agrupa los ejercicios bajo el módulo correspondiente. Las guías locales son material complementario del instructor; no sustituyen ni reproducen las instrucciones oficiales. El portal oficial y sus instrucciones están en inglés.

Antes de iniciar, revisa los [requisitos generales de los laboratorios](https://microsoftlearning.github.io/mslearn-azure-ai/lab-requirements.html). Además, cada ejercicio incluye requisitos específicos y puede necesitar permisos, cuota y recursos facturables.

## Limpieza y costes

Los laboratorios pueden crear recursos con coste. Usa una suscripción de laboratorio autorizada, sigue las instrucciones de limpieza del ejercicio y confirma en Azure Portal que no quedaron recursos activos. Consulta [Azure setup](prerequisites/azure.md) y [troubleshooting](troubleshooting/README.md).

## Recursos oficiales

- [Curso AI-200T00-A en Microsoft Learn](https://learn.microsoft.com/en-us/training/courses/ai-200t00)
- [Microsoft Certified: Azure AI Cloud Developer Associate](https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-cloud-developer-associate/)
- [Documentación de Azure](https://learn.microsoft.com/azure/)
