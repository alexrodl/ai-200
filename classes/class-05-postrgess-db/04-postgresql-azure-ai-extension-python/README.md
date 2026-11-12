# Demo - IA dentro de PostgreSQL con la extensión `azure_ai`

**Hotel Review Insights** es una web en Flask que analiza reseñas de hoteles en español, inglés y portugués. La app de Python **nunca llama a Microsoft Foundry directamente**: toda la IA se ejecuta como funciones SQL dentro de Azure Database for PostgreSQL, gracias a la extensión `azure_ai`. La web muestra en cada paso el SQL ejecutado y el tiempo que tardó.

## Qué vas a ver

| Paso | Esquema / función | Qué demuestra |
|---|---|---|
| 1 · Preparar | `CREATE EXTENSION azure_ai`, `azure_ai.set_setting()` | Instalar la extensión y configurar el endpoint y la key de Foundry |
| 2 · Enriquecer | `azure_cognitive.detect_language`, `analyze_sentiment`, `extract_key_phrases`, `azure_openai.create_embeddings` | Un solo `UPDATE` agrega idioma, sentimiento, frases clave y el embedding a todas las filas |
| 3 · Búsqueda semántica | `create_embeddings` + pgvector `<=>` | Búsqueda por significado y entre idiomas, con filtro por sentimiento |
| 4 · Laboratorio | `recognize_entities`, `recognize_pii_entities`, `summarize_abstractive`, ... | Probar cada función de Azure AI Language con cualquier texto |
| 5 · Operadores semánticos (preview) | `azure_ai.generate`, `azure_ai.is_true`, `azure_ai.extract` | RAG 100 % en SQL, filtros en lenguaje natural y extracción a JSON con `gpt-4.1-mini` |

## Recursos de Azure

`azdeploy.py` crea todo en el resource group `ai-200-postgres-04`:

- **Microsoft Foundry** (`AIServices`, S0, eastus2) con los despliegues `text-embedding-3-small` y `gpt-4.1-mini`. El mismo recurso expone Azure OpenAI y Azure AI Language.
- **Azure Database for PostgreSQL Flexible Server** (B1ms, v16, centralus) con autenticación de Microsoft Entra ID y `azure.extensions = AZURE_AI,VECTOR`.

> PostgreSQL usa otra región (`pg_location`) porque la suscripción puede tener restringida la creación de servidores en eastus2. La extensión llama a Foundry por HTTPS, así que no importa que estén en regiones distintas.

## Cómo ejecutarla

```powershell
cd 04-postgresql-azure-ai-extension-python
python azdeploy.py          # opciones 1, 2, 3 y luego 5 (genera .env.ps1)

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r client\requirements.txt

. .\.env.ps1
python client\app.py        # abre http://127.0.0.1:5000
```

En la web, sigue las pestañas en orden: **Ejecutar setup** → **Cargar 24 reseñas** → **Enriquecer con IA** (tarda unos 40 s).

> `.env` y `.env.ps1` contienen la key de Foundry y están en `.gitignore`. No los subas al repositorio.

## Ideas para comentar en clase

- **El dato no sale de la base de datos para ir a la app:** el servidor llama a Foundry. Así se puede enriquecer en lote con SQL, con triggers o con tareas programadas.
- **Composite types:** `analyze_sentiment` devuelve `(sentiment, positive_score, neutral_score, negative_score)`. Por eso se usa `SELECT * FROM azure_cognitive.analyze_sentiment(...)`.
- **Costo y latencia:** cada fila es una llamada HTTP. En el filtro con `is_true()`, primero se reducen los candidatos con búsqueda vectorial (barata) y solo después se usa el LLM (caro).
- **Seguridad:** la key queda guardada en la configuración de `azure_ai`, y solo los administradores y el rol `azure_ai_settings_manager` pueden leerla o cambiarla. En producción conviene usar managed identity.

## Limpieza

```powershell
az group delete --name ai-200-postgres-04 --yes --no-wait
```
