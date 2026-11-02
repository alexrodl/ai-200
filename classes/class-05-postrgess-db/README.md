# Class 05 - Azure Cosmos DB for NoSQL

## Datos de la clase

- **Fecha:** miércoles 4 de noviembre de 2026, de 19:00 a 22:00.
- **Duración:** 3 horas, incluido un corte de 15 minutos (20:22 - 20:37).
- **Tiempo neto de clase:** 2 horas y 45 minutos, con prioridad para la práctica.
- **Material de referencia:** presentación `AI-200T00-PowerPoint_04.es-ES.pptx`.
- **Bloques:** consultas y SDK, búsqueda vectorial y optimización de consultas en Azure Cosmos DB for NoSQL.

## Dónde quedamos

En la [clase 04](../class-04-aks-cosmos-db/README.md) terminamos el módulo de AKS y presentamos el modelo de recursos de Cosmos DB (diapositivas 1-9). Esta clase empieza con el primer ejercicio de Cosmos DB y completa el learning path.

## Objetivos

Al finalizar la clase, podrás:

- Conectarte a Cosmos DB for NoSQL con el SDK de Python y Microsoft Entra ID, y hacer operaciones CRUD.
- Elegir entre una lectura puntual y una consulta, y escribir consultas SQL con parámetros, dentro de una partición o entre particiones.
- Definir una directiva de vectores y ejecutar búsquedas de similitud con `VectorDistance`, con filtros de metadatos.
- Explicar la búsqueda híbrida (RRF) y el uso del change feed para mantener los embeddings actualizados.
- Ajustar la directiva de indexación (índices de rango, compuestos y vectoriales) y elegir el nivel de coherencia adecuado.

## Agenda

La suscripción temporal de laboratorio dura **2 horas desde que la inicias**. La agenda usa dos ventanas: la primera de 19:00 a 21:00 y la segunda desde las 21:00.

| Horario | Actividad | Diapositivas | Tipo |
|---|---|---|---|
| 19:00 - 19:05 | Iniciar la suscripción de laboratorio (ventana 1) y lanzar el despliegue de Lab 10 | - | Práctica |
| 19:05 - 19:15 | Repaso: clave de partición, RU, lectura puntual vs. consulta, consultas con parámetros | 5-9 | Teoría |
| 19:15 - 19:45 | **Lab 10** - Build a RAG document store | 10 | Práctica |
| 19:45 - 19:50 | Prueba de conocimientos del módulo 1, limpieza y lanzamiento del despliegue de Lab 11 | 11, 13 | Repaso |
| 19:50 - 20:05 | Búsqueda vectorial: directiva de vectores, `VectorDistance`, filtros, RRF y change feed | 14-20 | Teoría |
| 20:05 - 20:22 | **Lab 11** (parte 1) - Completar `vector_functions.py` | 21 | Práctica |
| 20:22 - 20:37 | **Corte** | - | - |
| 20:37 - 20:52 | **Lab 11** (parte 2) - Búsqueda por similitud y con filtros | 21 | Práctica |
| 20:52 - 21:00 | Prueba de conocimientos del módulo 2 y limpieza (la ventana 1 termina a las 21:00) | 22, 24 | Repaso |
| 21:00 - 21:15 | Iniciar la ventana 2, lanzar el despliegue de Lab 12 y ver la optimización: índices y coherencia | 25-32 | Teoría |
| 21:15 - 21:45 | **Lab 12** - Optimize query performance with vector indexes | 33 | Práctica |
| 21:45 - 21:50 | Prueba de conocimientos del módulo 3 | 34, 36 | Repaso |
| 21:50 - 22:00 | Debate en grupo, cierre y tareas | 37-38 | Cierre |

**Resultado:** unos 100 minutos de práctica y 40 minutos de teoría. **Al final de esta clase se completa el learning path de Cosmos DB.** Azure Database for PostgreSQL empieza en la clase 06.

## Temas y resumen

### Consultas con Azure Cosmos DB for NoSQL (Lab 10)

- **Jerarquía:** cuenta → base de datos → contenedor → elemento. Los contenedores no tienen esquema fijo.
- **Clave de partición:** elige una propiedad de alta cardinalidad que coincida con tu consulta más frecuente. No se puede cambiar después.
- **Rendimiento:** manual (RU/s fijas) o escalado automático (entre el 10 % y el 100 % del máximo). En el Lab 13 se usa el modo serverless.
- **SDK:** un único `CosmosClient` para toda la aplicación (*singleton*). Usa `create_*_if_not_exists` para que la inicialización sea idempotente.
- **Lectura puntual vs. consulta:** `read_item(id, partition_key)` cuesta alrededor de 1 RU por 1 KB. `query_items()` sirve para filtrar y buscar, y su costo varía.
- **Consultas:** usa siempre parámetros (`@category`). Si la consulta puede limitarse a una partición, es más barata que una consulta entre particiones (`enable_cross_partition_query=True`).

### Búsqueda vectorial (Lab 11)

- La búsqueda vectorial está **integrada** en Cosmos DB: guardas el embedding junto al documento y no necesitas otra base de datos vectorial.
- La **directiva de vectores** (ruta, `dataType`, `dimensions` y `distanceFunction`) se define **al crear el contenedor** y no se puede modificar después. `dimensions` tiene que coincidir con el modelo de embeddings.
- Patrón de consulta: `SELECT TOP N ... ORDER BY VectorDistance(c.embedding, @queryVector)`. Usa el mismo modelo de embeddings para los documentos y para la consulta.
- **Filtros de metadatos** en el `WHERE` para acotar resultados (categoría, fecha, permisos). **Búsqueda híbrida** con `ORDER BY RANK RRF(VectorDistance(...), FullTextScore(...))`, que requiere una directiva e índice de texto completo.
- **Change feed** + Azure Functions para regenerar embeddings cuando cambia el contenido. El procesamiento debe ser idempotente.

### Optimización del rendimiento de las consultas (Lab 12)

- La indexación por defecto (`/*`) es cómoda para empezar, pero cara a escala. **Excluye las rutas de los embeddings** de los índices de rango.
- **Índices compuestos:** son obligatorios para `ORDER BY` con varias propiedades. El orden de las propiedades tiene que coincidir con el de la consulta.
- **Índices vectoriales:** `flat` (exacto, hasta 505 dimensiones), `quantizedFlat` (comprimido) y `diskANN` (escala de producción). `quantizedFlat` y `diskANN` necesitan alrededor de 1000 vectores para ser efectivos.
- **Métricas de consulta:** si se recuperan muchos más documentos de los que se devuelven, faltan índices.
- **Coherencia:** `Session` es la opción adecuada para la mayoría de las aplicaciones de IA. `Strong` y `Bounded Staleness` duplican el costo en RU de las lecturas. `Eventual` sirve para análisis y procesos en segundo plano.

## Ejercicios

Los ejercicios forman parte del material oficial del curso. Crear la cuenta de Cosmos DB tarda entre 5 y 10 minutos, así que lanza el script al principio de cada ejercicio y sigue con la teoría mientras termina.

| Ejercicio | Actividad | Tiempo estimado | Archivos del laboratorio |
|---|---|---:|---|
| [Build a RAG document store on Azure Cosmos DB for NoSQL](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/cosmosdb/01-build-rag-document-store.html) | **Lab 10.** Crear un almacén de fragmentos de documentos para RAG (clave de partición `/documentId`), completar las funciones de `rag_functions.py` y consultar desde Query Explorer. | 30 minutos | Starter oficial `cosmosdb-build-query-python.zip` |
| [Build a semantic search application with Azure Cosmos DB for NoSQL](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/cosmosdb/02-build-semantic-search.html) | **Lab 11.** Crear un contenedor con directiva de vectores (256 dimensiones, coseno, `diskANN`) e implementar búsquedas por similitud y con filtros. | 30 minutos | Starter oficial `cosmosdb-implement-vector-python.zip` |
| [Optimize query performance with vector indexes on Azure Cosmos DB for NoSQL](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/cosmosdb/03-optimize-query-performance.html) | **Lab 12.** Comparar RU y latencia entre `flat`, `quantizedFlat` y `diskANN` con 500 documentos. | 30 minutos | Starter oficial `cosmosdb-optimize-query-python.zip` |
| *Opcional:* [Build persistent memory for an AI assistant on Azure Cosmos DB for NoSQL](https://microsoftlearning.github.io/mslearn-azure-ai/instructions/cosmosdb/04-persisent-agent-memory.html) | **Lab 13.** Memoria de un asistente con claves de partición jerárquicas (`/tenantId`, `/threadId`) y TTL. | 30 minutos | Starter oficial (ver el ejercicio) |

> **Posibles tareas para casa:**
> - El **Lab 13 (opcional)** es tarea. Puedes hacerlo con la ventana 2, que sigue activa hasta unos 60 minutos después de la clase.
> - Si la clase se retrasa, el **Lab 12** se hace como demostración del instructor y queda como tarea.
> - Si ya hiciste el **Lab 10** en casa después de la clase 04, usa ese tiempo para repasar Query Explorer o adelantar el Lab 11.

## Trabajar con la suscripción temporal de laboratorio (2 horas)

- **Primero lanza `azdeploy.py` y después lee o edita el código.** Puedes completar las funciones de Python mientras se crea la cuenta.
- **Elimina el Resource Group de cada ejercicio** antes de lanzar el siguiente. Cada ejercicio crea su propia cuenta de Cosmos DB.
- **No empieces un ejercicio con menos de 30 minutos restantes** en la ventana.
- **Trabaja en una carpeta local.** El código que escribas se conserva aunque la suscripción caduque.

### Si la suscripción caduca a mitad de un ejercicio

1. Inicia una nueva sesión de laboratorio, ejecuta `az login` y comprueba con `az account show` que estás en la suscripción nueva.
2. Vuelve a ejecutar `azdeploy.py`: crea la cuenta, asigna el rol de datos de Entra ID y **genera de nuevo `.env` / `.env.ps1`** con el nuevo endpoint.
3. Vuelve a cargar las variables de entorno y reinicia la aplicación Flask. Tus funciones de Python ya completadas siguen funcionando.
4. Si aparece un error 403 de datos justo después de crear la cuenta, espera unos minutos a que se propague la asignación del rol `Cosmos DB Built-in Data Contributor`.

## Preguntas para revisar

- Si una aplicación lee con frecuencia todos los registros de un usuario, ¿qué clave de partición usarías?
- ¿Cuándo usarías `read_item()` en lugar de `query_items()`?
- ¿Por qué hay que definir la directiva de vectores antes de crear el contenedor?
- ¿Qué pasa si las dimensiones de la directiva no coinciden con las del modelo de embeddings?
- ¿Qué consulta usarías para combinar la búsqueda semántica con la búsqueda por palabras clave exactas (por ejemplo, códigos de error)?
- Una consulta filtra por `documentType` y ordena por `uploadDate DESC`. ¿Qué índice compuesto necesita?
- ¿Por qué `Session` es el nivel de coherencia recomendado para la mayoría de las aplicaciones de IA?

## Recursos de Microsoft Learn

- [Learning path: Develop AI solutions with Azure Cosmos DB for NoSQL](https://learn.microsoft.com/training/paths/develop-ai-solutions-azure-cosmos-db/)
  - [Build queries for Azure Cosmos DB for NoSQL](https://learn.microsoft.com/training/modules/build-query-azure-cosmos-db/)
  - [Implement vector search on Azure Cosmos DB for NoSQL](https://learn.microsoft.com/training/modules/implement-vector-search-azure-cosmos-db/)
  - [Optimize query performance for Azure Cosmos DB for NoSQL](https://learn.microsoft.com/training/modules/optimize-query-performance-azure-cosmos-db/)
- [Documentación de Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/nosql/)

## Preparación y cierre

Antes de la clase, comprueba que tienes Azure CLI, Python 3.12 o posterior y Visual Studio Code, y que puedes iniciar la suscripción de laboratorio. Los ejercicios crean cuentas de Cosmos DB facturables. Al terminar cada uno, elimina su Resource Group (`az group delete --name <rg-name> --no-wait --yes`) y comprueba en Azure Portal que no queden recursos activos.

**Próxima clase:** Azure Database for PostgreSQL (`AI-200T00-PowerPoint_05.es-ES.pptx`).
