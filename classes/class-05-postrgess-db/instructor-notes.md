# Instructor Notes - Class 05

> Notas complementarias del instructor (MCT). No reemplazan ni reproducen el material oficial de Microsoft. Las diapositivas se refieren a `AI-200T00-PowerPoint_04.es-ES.pptx`.

## Objective

Completar el learning path de Cosmos DB for NoSQL con los tres ejercicios oficiales hechos en clase, para que la clase 06 empiece directamente con Azure Database for PostgreSQL.

## Teaching Goal

- Las tres decisiones de diseño que no se pueden cambiar después: **clave de partición, directiva de vectores y (en la práctica) el modelo de embeddings**.
- Pensar el costo en **RU**: mostrar `x-ms-request-charge` en cada ejercicio.
- Hacer un puente con AKS/ACA: estas aplicaciones Flask/API son las que se desplegarían en los contenedores de las clases anteriores, autenticadas con Managed Identity / Workload Identity.

## Before the Class

- [ ] Descargar los ZIP de inicio de los Labs 10, 11 y 12 y revisar que el `azdeploy.py` de cada uno pide `rg` y `location`.
- [ ] Confirmar con XtremeLabs que la región elegida tiene capacidad para Cosmos DB y que la suscripción permite crear **asignaciones de rol** (Lab 10 y 13 asignan `Cosmos DB Built-in Data Contributor` al usuario).
- [ ] En **tu propia suscripción**, tener una cuenta del Lab 12 ya desplegada **con los 500 documentos cargados** en los tres contenedores. Es el plan B para hacer la comparación como demo.
- [ ] Preguntar al principio quién hizo el Lab 10 en casa después de la clase 04.

## Detailed Agenda

| Horario | Bloque | Diapos | Notas |
|---|---|---|---|
| 19:00 - 19:05 | Inicio de la ventana 1. `az login`, registrar `Microsoft.DocumentDB` y `azdeploy.py` del Lab 10 | - | La cuenta tarda 5-10 minutos |
| 19:05 - 19:15 | Repaso del módulo 1 | 5-9 | Partición, RU, lectura puntual vs. consulta y parámetros. Ya presentado en la clase 04: solo las ideas clave |
| 19:15 - 19:45 | Lab 10 | 10 | `rag_functions.py`: guardar fragmentos, obtener por documento, buscar por metadatos y lectura puntual. Cerrar con Query Explorer |
| 19:45 - 19:50 | KC M1 y resumen | 11, 13 | Eliminar el RG del Lab 10 y **lanzar ya el despliegue del Lab 11** |
| 19:50 - 20:05 | Módulo 2: búsqueda vectorial | 14-20 | Mientras se despliega el Lab 11 |
| 20:05 - 20:22 | Lab 11 (parte 1) | 21 | Completar `store_vector_document`, `vector_similarity_search` y `filtered_vector_search`. Revisar `setup_container.py` |
| 20:22 - 20:37 | Corte | - | - |
| 20:37 - 20:52 | Lab 11 (parte 2) | 21 | Ejecutar Flask, cargar los 12 tickets, buscar por similitud y con filtros |
| 20:52 - 21:00 | KC M2, resumen y limpieza | 22, 24 | La ventana 1 termina a las 21:00 |
| 21:00 - 21:15 | Inicio de la ventana 2, `azdeploy.py` del Lab 12 y módulo 3 | 25-32 | Mientras se crean la cuenta y los tres contenedores |
| 21:15 - 21:45 | Lab 12 | 33 | Cargar los 500 tickets y comparar RU y tiempos entre flat, quantizedFlat y diskANN, con y sin filtro |
| 21:45 - 21:50 | KC M3 y resumen | 34, 36 | - |
| 21:50 - 22:00 | Debate (elegir 1 pregunta), cierre y tareas | 37-38 | Tarea opcional: Lab 13 en la ventana 2 (activa hasta ~23:00) |

### Contingencias

- **Si muchos hicieron el Lab 10 en casa:** usar los 30 minutos para ampliar el Lab 11 (por ejemplo, probar `VectorDistance` desde Query Explorer) o empezar el Lab 12 en la ventana 1.
- **A las 20:22, si el Lab 11 no tiene las funciones completadas:** recortar el módulo 3 a 10 minutos (diapositivas 28-32).
- **Si a las 21:20 la mitad del grupo no tiene la cuenta del Lab 12 creada:** hacer la comparación en pantalla con la cuenta preparada (plan B) y dejar el Lab 12 como tarea en la ventana 2.
- **PostgreSQL no cabe en esta clase.** No adelantes las diapositivas del PPT 05 si sobran minutos: es mejor dedicarlos a la práctica y a dudas.

## Key Concepts and Talking Points

### Module 1 (diapositivas 5-9)

- La partición lógica es el valor de la clave. La partición física la gestiona Azure. Una clave con mala distribución provoca **particiones activas (hot partitions)** y throttling (HTTP 429).
- Escalado automático: el mínimo es siempre el 10 % del máximo. Con un máximo de 1000 RU/s, baja hasta 100 RU/s.
- Lo que aumenta el costo en RU: elementos más grandes, más índices, mayor coherencia y consultas entre particiones.
- `get_database_client()` / `get_container_client()` son referencias ligeras, no conexiones.
- `upsert_item` es útil para guardar en caché salidas del modelo. Con `_etag` se implementa la concurrencia optimista.
- Las comparaciones de cadenas distinguen mayúsculas y minúsculas: `LOWER()` / `UPPER()` o `CONTAINS(x, y, true)`.

### Module 2 (diapositivas 15-20)

- La capacidad de búsqueda vectorial se habilita **en la cuenta** (el Lab 11 lo hace con `EnableNoSQLVectorSearch`).
- `dimensions` = salida del modelo (el Lab 11 usa embeddings precalculados de 256 dimensiones, sin Foundry). Para `text-embedding-ada-002` serían 1536.
- Coseno con embeddings de Azure OpenAI (vienen normalizados).
- Con `VectorDistance` y coseno, una puntuación más alta indica más similitud. Comentar el rango orientativo de las diapositivas y aclarar que depende del modelo.
- Siempre `TOP N`. Para RAG, entre 5 y 10 resultados suele ser suficiente.
- Búsqueda híbrida con RRF: buen ejemplo con códigos de error ("error 0x80070005 al instalar").
- Change feed: el contenedor de *leases* va separado de los datos. Guarda un hash del contenido para no regenerar embeddings cuando solo cambian los metadatos.

### Module 3 (diapositivas 26-32)

- La directiva por defecto es `includedPaths: /*`. La clave de partición **no** se indexa automáticamente si excluyes todo por defecto: hay que incluirla.
- Índice compuesto: sin él, un `ORDER BY` con varias propiedades **falla**, no solo va más lento.
- La transformación de índices es asíncrona: primero se agrega el índice nuevo, se espera a que termine y después se quita el antiguo.
- Tipos de índice vectorial y la regla de alrededor de 1000 vectores: por debajo, `quantizedFlat` y `diskANN` hacen una búsqueda por fuerza bruta. Es justo lo que se ve en el Lab 12 con 500 documentos por contenedor. **Pregunta para el grupo:** ¿por qué las diferencias de RU entre índices son pequeñas en el laboratorio?
- Coherencia: `Session` por defecto. Los tokens de sesión se gestionan solos dentro de un cliente; entre servicios distintos hay que pasarlos.

## Demo Suggestions

1. **Lectura puntual vs. consulta (3 minutos, después del Lab 10):** en Data Explorer, leer el mismo elemento con una lectura puntual y con `SELECT * FROM c WHERE c.id = @id` sin clave de partición. Comparar el *Request Charge* en *Query Stats*.
2. **Consulta vectorial en Query Explorer (3 minutos, en el Lab 11):** ejecutar una consulta `VectorDistance` con un vector de ejemplo y mostrar las puntuaciones.
3. **Índice compuesto que falta (3 minutos, módulo 3):** ejecutar `ORDER BY c.category, c.createdAt DESC` sin índice compuesto, mostrar el error, agregar el índice en *Settings > Indexing Policy* y repetir. Usar el contenedor del Lab 12 en la cuenta del instructor.

## Likely Student Questions

| Tipo | Pregunta | Respuesta breve |
|---|---|---|
| Principiante | ¿Cosmos DB es SQL o NoSQL? | La API for NoSQL guarda JSON y usa una sintaxis parecida a SQL para consultar. Cada consulta trabaja sobre un solo contenedor (no hay JOIN entre contenedores) |
| Práctica | ¿Por qué me da 403 si soy Owner? | Los roles de datos (*data plane*) son distintos de los de control. Necesitas `Cosmos DB Built-in Data Contributor` y esperar a que se propague |
| Práctica | ¿Cómo sé cuántas RU consume una consulta? | `x-ms-request-charge` en la respuesta, o *Query Stats* en Data Explorer |
| Troubleshooting | Error de dimensiones al insertar un vector | La longitud del array no coincide con `dimensions` de la directiva. Hay que crear un contenedor nuevo o usar el modelo correcto |
| Arquitectura | ¿Cosmos DB, Azure AI Search o pgvector para RAG? | Si los datos operativos ya están en Cosmos DB, la búsqueda integrada evita sincronizar dos almacenes. AI Search aporta más funciones de búsqueda (ranking semántico, skillsets). pgvector conviene si el modelo es relacional (clase 06) |
| Arquitectura | ¿Qué pasa si cambio de modelo de embeddings? | Cambian las dimensiones y el espacio vectorial: contenedor nuevo, regenerar todos los embeddings y migrar. Diseñarlo desde el principio (por ejemplo, guardar el nombre del modelo en el documento) |
| Producción | ¿Coherencia Strong para estar seguros? | Duplica el costo en RU de las lecturas, aumenta la latencia y no se admite con varias regiones de escritura. `Session` cubre "leer lo que escribí" |
| Producción | ¿Serverless o provisionado? | Serverless para cargas intermitentes y desarrollo. Provisionado o escalado automático para cargas sostenidas y escritura en varias regiones |
| Certificación | ¿Entra `VectorDistance` en el examen? | No se puede asegurar qué preguntas habrá. La búsqueda vectorial y la indexación son habilidades centrales del learning path |

## AI-200 Exam Tips

> Se basan en los conceptos del curso oficial. No son preguntas del examen. Revisa el [skills outline de la certificación](https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-cloud-developer-associate/) para la versión vigente.

- **Clave de partición:** alta cardinalidad + filtro más frecuente. Evita booleanos y marcas de tiempo.
- **`read_item()` vs. `query_items()`:** si conoces `id` y la clave de partición, usa siempre la lectura puntual.
- **Directiva de vectores:** `dataType`, `dimensions` (igual al modelo) y `distanceFunction`. No se puede cambiar después de crear el contenedor.
- **Patrón de consulta:** `TOP N` + `ORDER BY VectorDistance(...)` con `@queryVector` como parámetro.
- **Híbrida = `ORDER BY RANK RRF(VectorDistance, FullTextScore)`**, que requiere una directiva e índice de texto completo.
- **Índices vectoriales:** `flat` es exacto, hasta 505 dimensiones y para pocos vectores; `quantizedFlat` para volumen medio; `diskANN` para gran escala.
- **Índice compuesto:** primero la propiedad del filtro de igualdad y después la de ordenación. El orden tiene que coincidir con `ORDER BY`.
- **Métricas:** si se recuperan muchos más documentos de los que se devuelven, faltan índices.
- **Coherencia:** `Session` por defecto. `Strong` y `Bounded Staleness` cuestan el doble en lecturas. `Eventual` para análisis.

## Notes on the Official Slides

- **Diapositiva 30:** la celda "5:05" de la columna de dimensiones máximas de `flat` es un error de traducción o formato. El valor correcto es **505**.
- **Diapositiva 32:** "Seguro: solo escenarios financieros o normativos" corresponde a **Strong** (fuerte). Aclararlo para no confundirlo con un nivel distinto.
- En las diapositivas de **resumen** (13, 24 y 36) se repite el párrafo del resumen del módulo 1. En las de los módulos 2 y 3 sobra.
- Las diapositivas de ejercicio tienen el marcador "Personaliza esta diapositiva...". Sustitúyelo por las instrucciones de XtremeLabs.
- Para la clase 06: en la diapositiva 6 del PPT 05 (PostgreSQL) aparece el título "Exploración de Azure Cosmos DB for NoSQL" por error.

## Common Mistakes

| Error | Causa | Solución |
|---|---|---|
| `Forbidden (403)` en operaciones de datos | Falta el rol de datos o todavía no se ha propagado | Ejecutar la opción del script que configura Entra ID y esperar de 2 a 5 minutos |
| La aplicación Flask no encuentra el endpoint | No se cargó `.env` / `.env.ps1` en la terminal actual | `. .\.env.ps1` (PowerShell) o `source .env` (Bash) |
| Consulta lenta o costosa sin clave de partición | Consulta entre particiones | Pasar `partition_key=` o filtrar por la clave en el `WHERE` |
| Error en `ORDER BY` con dos propiedades | Falta el índice compuesto | Agregarlo a la directiva de indexación |
| La sesión de XtremeLabs caducó | Ventana de 2 horas | Ver "Si la suscripción caduca" en el [README](README.md) |
