# Modelos de embeddings: opciones pagas y gratuitas

*Actualizado: 2 de noviembre de 2026*

## Introducción

Los modelos que pasan texto a vectores **no son LLM** como GPT o Claude, aunque muchos se construyen a partir de ellos. Se llaman **modelos de embeddings**: no generan texto, solo devuelven el vector.

## Modelos pagos (por API)

| Proveedor | Modelos | Dimensiones | Comentario |
|---|---|---|---|
| **OpenAI / Azure OpenAI** | `text-embedding-3-small`, `text-embedding-3-large`, `ada-002` | 1536 / 3072 / 1536 | El que usan las slides. El más natural si los alumnos están en Azure. |
| **Google** | `gemini-embedding-001`, Gemini Embedding 2 | Hasta 3072 | Muy fuerte en multilingüe |
| **Voyage AI** (ahora de MongoDB) | Serie voyage-4 | Hasta 2048 | Suele liderar en calidad de búsqueda |
| **Cohere** | `embed-v4` | 256 a 1536 | Multimodal (texto e imagen) y multilingüe empresarial |

Según una comparativa de julio de 2026:

- **Voyage-4-large** es el mejor en calidad de búsqueda por API (~US$0,12 por millón de tokens).
- **Gemini Embedding 001** es el mejor todoterreno (~US$0,15 por millón de tokens).
- **La familia text-embedding-3 de OpenAI** sigue siendo la opción por defecto más segura para búsqueda de uso general.

**Los precios son muy bajos.** Los modelos de OpenAI cuestan entre US$0,02 y US$0,13 por millón de tokens. Por ejemplo, con `text-embedding-3-small`, convertir 1000 documentos de unas 500 palabras cada uno cuesta alrededor de un centavo de dólar. Para una demo de clase, el costo es prácticamente cero.

## Modelos gratuitos (open source, los corrés vos)

Se descargan y se ejecutan en tu propia máquina o servidor. No pagás por token, pero sí necesitás hardware.

| Modelo | Dimensiones | Comentario |
|---|---|---|
| **BGE-M3** (BAAI) | 1024 | Licencia MIT, más de 100 idiomas, entradas de hasta 8192 tokens. Muy buena opción para español. |
| **Qwen3-Embedding** (Alibaba) | Hasta 4096 (8B) | Licencia Apache 2.0, primer puesto en el ranking MTEB multilingüe. La versión 8B necesita GPU; hay versiones más chicas. |
| **Granite Embedding Multilingual R2** (IBM) | 768 | Publicado en mayo de 2026, con modelos de 97M y 311M de parámetros, licencia Apache 2.0. Liviano, corre bien sin GPU. |
| **nomic-embed-text** | 768 | Muy fácil de usar con **Ollama** en una laptop. Ideal para demos sin conexión. |

**Para una demo en clase sin gastar nada**, lo más simple es Ollama con `nomic-embed-text` o `bge-m3`: se instala en minutos y corre en una laptop común.

```bash
ollama pull nomic-embed-text
curl http://localhost:11434/api/embed -d '{"model": "nomic-embed-text", "input": "mi WiFi no funciona"}'
```

Gemini también suele tener un nivel gratuito con límites de uso en su API. Revisá las condiciones actuales antes de recomendarlo.

## Lo que importa para Cosmos DB

- **Las dimensiones del modelo tienen que coincidir con la política vectorial.** Gemini o `text-embedding-3-large` (3072) entran en diskANN o quantizedFlat (hasta 4096), pero no en flat (505). Qwen3-Embedding-8B (4096) queda justo en el límite.
- **Muchos modelos modernos permiten recortar dimensiones** (técnica *Matryoshka*). Por ejemplo, podés pedirle a `text-embedding-3-large` vectores de 1024 en lugar de 3072: ocupan un tercio del espacio con una pérdida de calidad chica.
- **Elegir modelo es una decisión que no se cambia fácil.** Cambiar de modelo implica crear un contenedor nuevo y volver a generar todos los embeddings.
- **No te guíes solo por los rankings.** Compará al menos dos candidatos con consultas y documentos etiquetados de tu propia aplicación antes de construir el índice completo.

## Recomendación para el curso

Usá `text-embedding-3-small` de Azure OpenAI para las demos: encaja con el ecosistema Azure del curso y es muy barato. Mencioná BGE-M3 u Ollama como alternativa gratuita para los alumnos que quieran practicar sin una suscripción.

## Fuentes

- [9 Best Embedding Models for RAG in 2026 (Techsy)](https://techsy.io/en/blog/best-embedding-models-for-rag)
- [Best Embedding Model APIs (2026) (Stork)](https://www.stork.ai/blog/best-embedding-model-apis-2026)
- [13 Best Embedding Models in 2026 (Elephas)](https://elephas.app/blog/best-embedding-models.md)
- [Best Embedding Models in 2026: OpenAI vs Gemini vs Open (DataLLMLab)](https://www.datallmlab.com/blog/best-embedding-models.html)
- [Granite Embedding Multilingual R2 (Toolhalla)](https://toolhalla.ai/blog/granite-embedding-multilingual-r2)
- [Best Embedding Models in 2026 (OpenRouter)](https://openrouter.ai/blog/insights/best-embedding-models-2026/)
