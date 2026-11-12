"""
Hotel Review Insights - a Flask demo of the azure_ai extension for
Azure Database for PostgreSQL.

Key idea: the Python app NEVER calls Microsoft Foundry directly. Every AI
operation (embeddings, sentiment, key phrases, entities, PII, summaries and
LLM-based semantic operators) is a SQL function executed INSIDE PostgreSQL by
the azure_ai extension. The app only sends SQL and shows it on screen.
"""
import json
import logging
import os
import time

import psycopg
from azure.identity import DefaultAzureCredential
from flask import Flask, jsonify, render_template, request
from psycopg.rows import dict_row

logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)

EMBEDDING_DEPLOYMENT = os.environ.get("EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
CHAT_DEPLOYMENT = os.environ.get("CHAT_DEPLOYMENT", "gpt-4.1-mini")

# -----------------------------------------------------------------------------
# Database connection (Microsoft Entra ID token as the password)
# -----------------------------------------------------------------------------
_credential = DefaultAzureCredential()
_token = None


def get_connection():
    """Open a connection using a cached Microsoft Entra access token."""
    global _token
    host = os.environ.get("DB_HOST")
    user = os.environ.get("DB_USER")
    if not host or not user:
        raise ValueError("DB_HOST and DB_USER must be set. Run: . ..\\.env.ps1")

    if _token is None or _token.expires_on - time.time() < 300:
        _token = _credential.get_token("https://ossrdbms-aad.database.windows.net/.default")

    return psycopg.connect(
        host=host,
        dbname=os.environ.get("DB_NAME", "postgres"),
        user=user,
        password=_token.token,
        sslmode="require",
        autocommit=True,
        row_factory=dict_row,
        # ClientCursor lets us "mogrify" the query to display the exact SQL sent.
        cursor_factory=psycopg.ClientCursor,
    )


def run_sql(sql, params=None, display_sql=None):
    """Execute one SQL statement and return a JSON-friendly payload for the UI."""
    started = time.perf_counter()
    with get_connection() as conn, conn.cursor() as cur:
        shown = display_sql or cur.mogrify(sql, params)
        cur.execute(sql, params)
        rows = cur.fetchall() if cur.description else []
        rowcount = cur.rowcount
    return {
        "sql": shown.strip(),
        "rows": rows,
        "rowcount": rowcount,
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
    }


def api(handler):
    """Wrap an endpoint so every error is returned as JSON to the UI."""
    def wrapper(*args, **kwargs):
        try:
            return jsonify(handler(*args, **kwargs))
        except Exception as exc:  # noqa: BLE001 - demo app: surface any DB/AI error
            return jsonify({"error": str(exc).strip()}), 400
    wrapper.__name__ = handler.__name__
    return wrapper


# -----------------------------------------------------------------------------
# 1. Setup: extensions, azure_ai settings and table
# -----------------------------------------------------------------------------
SETUP_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS azure_ai;

-- Tell azure_ai where the Foundry endpoints are and which key to use.
SELECT azure_ai.set_setting('azure_openai.endpoint',            %(openai_endpoint)s);
SELECT azure_ai.set_setting('azure_openai.subscription_key',    %(key)s);
SELECT azure_ai.set_setting('azure_cognitive.endpoint',         %(language_endpoint)s);
SELECT azure_ai.set_setting('azure_cognitive.subscription_key', %(key)s);

CREATE TABLE IF NOT EXISTS hotel_reviews (
    id             serial PRIMARY KEY,
    hotel          text NOT NULL,
    city           text NOT NULL,
    rating         int,
    review_text    text NOT NULL,
    -- Columns filled by AI (azure_ai) in step 2
    language       text,
    sentiment      text,
    positive_score float8,
    neutral_score  float8,
    negative_score float8,
    key_phrases    text[],
    embedding      vector(1536)
);

CREATE INDEX IF NOT EXISTS hotel_reviews_embedding_idx
    ON hotel_reviews USING hnsw (embedding vector_cosine_ops);
"""


@app.post("/api/setup")
@api
def setup():
    key = os.environ.get("AZURE_AI_KEY", "")
    params = {
        "openai_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
        "language_endpoint": os.environ.get("AZURE_LANGUAGE_ENDPOINT", ""),
        "key": key,
    }
    if not all(params.values()):
        raise ValueError("Missing AZURE_OPENAI_ENDPOINT, AZURE_LANGUAGE_ENDPOINT or AZURE_AI_KEY.")
    # Never show the real key on screen.
    masked = {**params, "key": key[:4] + "****************"}
    with get_connection() as conn, conn.cursor() as cur:
        display = cur.mogrify(SETUP_SQL, masked)
    result = run_sql(SETUP_SQL, params, display_sql=display)

    versions = run_sql("""
        SELECT extname AS extension, extversion AS version
        FROM pg_extension WHERE extname IN ('azure_ai', 'vector') ORDER BY 1;
    """)
    result["rows"] = versions["rows"]
    return result


@app.post("/api/load")
@api
def load_data():
    """Insert the raw reviews. Only text: no AI yet."""
    with open(os.path.join(os.path.dirname(__file__), "sample_reviews.json"), encoding="utf-8") as f:
        reviews = json.load(f)["reviews"]
    sql = """
        INSERT INTO hotel_reviews (hotel, city, rating, review_text)
        SELECT r.hotel, r.city, r.rating, r.review_text
        FROM jsonb_to_recordset(%(reviews)s::jsonb)
             AS r(hotel text, city text, rating int, review_text text)
        WHERE NOT EXISTS (SELECT 1 FROM hotel_reviews h WHERE h.review_text = r.review_text);
    """
    result = run_sql(sql, {"reviews": json.dumps(reviews, ensure_ascii=False)})
    # The JSON payload is long; show a shortened version in the UI.
    result["sql"] = result["sql"][:600] + " ... ]'::jsonb) ..."
    return result


@app.post("/api/reset")
@api
def reset():
    return run_sql("DROP TABLE IF EXISTS hotel_reviews;")


# -----------------------------------------------------------------------------
# 2. Enrich every review with AI using a single UPDATE
# -----------------------------------------------------------------------------
ENRICH_SQL = """
WITH detected AS (
    -- Azure AI Language: detect the language of each pending review
    SELECT id, (azure_cognitive.detect_language(review_text)).iso6391_name AS lang
    FROM hotel_reviews
    WHERE embedding IS NULL
)
UPDATE hotel_reviews r
SET language = d.lang,
    -- Azure AI Language: sentiment (returns a composite type)
    (sentiment, positive_score, neutral_score, negative_score) = (
        SELECT s.sentiment, s.positive_score, s.neutral_score, s.negative_score
        FROM azure_cognitive.analyze_sentiment(r.review_text, d.lang) AS s
    ),
    -- Azure AI Language: key phrases (returns text[])
    key_phrases = azure_cognitive.extract_key_phrases(r.review_text, d.lang),
    -- Foundry model: embedding vector (returns real[] -> cast to vector)
    embedding = azure_openai.create_embeddings(%(deployment)s, r.review_text)::vector
FROM detected d
WHERE r.id = d.id;
"""


@app.post("/api/enrich")
@api
def enrich():
    return run_sql(ENRICH_SQL, {"deployment": EMBEDDING_DEPLOYMENT})


@app.get("/api/reviews")
@api
def reviews():
    data = run_sql("""
        SELECT id, hotel, city, rating, review_text, language, sentiment,
               round(positive_score::numeric, 2) AS positive,
               round(negative_score::numeric, 2) AS negative,
               key_phrases, embedding IS NOT NULL AS has_embedding
        FROM hotel_reviews ORDER BY hotel, id;
    """)
    data["stats"] = run_sql("""
        SELECT hotel, city, count(*) AS reviews,
               round(avg(rating), 1) AS avg_rating,
               count(*) FILTER (WHERE sentiment = 'positive') AS positive,
               count(*) FILTER (WHERE sentiment IN ('neutral', 'mixed')) AS neutral,
               count(*) FILTER (WHERE sentiment = 'negative') AS negative
        FROM hotel_reviews GROUP BY hotel, city ORDER BY hotel;
    """)
    return data


# -----------------------------------------------------------------------------
# 3. Semantic search: the query embedding is ALSO generated inside SQL
# -----------------------------------------------------------------------------
@app.post("/api/search")
@api
def search():
    body = request.get_json()
    sentiment = body.get("sentiment") or None
    sql = """
        WITH q AS (
            SELECT azure_openai.create_embeddings(%(deployment)s, %(query)s)::vector AS v
        )
        SELECT r.id, r.hotel, r.city, r.rating, r.sentiment, r.review_text,
               round((1 - (r.embedding <=> q.v))::numeric, 3) AS similarity
        FROM hotel_reviews r, q
        WHERE r.embedding IS NOT NULL
          AND (%(sentiment)s::text IS NULL OR r.sentiment = %(sentiment)s::text)
        ORDER BY r.embedding <=> q.v
        LIMIT 5;
    """
    return run_sql(sql, {"deployment": EMBEDDING_DEPLOYMENT,
                         "query": body["query"], "sentiment": sentiment})


# -----------------------------------------------------------------------------
# 4. Text lab: every Azure AI Language function, one at a time
# -----------------------------------------------------------------------------
ANALYZE_SQL = {
    "language": "SELECT * FROM azure_cognitive.detect_language(%(text)s);",
    "sentiment": "SELECT * FROM azure_cognitive.analyze_sentiment(%(text)s, %(lang)s);",
    "key_phrases": "SELECT unnest(azure_cognitive.extract_key_phrases(%(text)s, %(lang)s)) AS key_phrase;",
    "entities": "SELECT * FROM unnest(azure_cognitive.recognize_entities(%(text)s, %(lang)s));",
    "pii": """
        SELECT p.redacted_text, e.text AS entity, e.category, e.confidence_score
        FROM azure_cognitive.recognize_pii_entities(%(text)s, %(lang)s) AS p
        LEFT JOIN LATERAL unnest(p.entities) AS e ON true;
    """,
    "summary": "SELECT unnest(azure_cognitive.summarize_abstractive(%(text)s, %(lang)s, 2)) AS summary;",
    "embedding": """
        SELECT vector_dims(v) AS dimensions, (v::real[])[1:6] AS first_values
        FROM (SELECT azure_openai.create_embeddings(%(deployment)s, %(text)s)::vector AS v) AS e;
    """,
}


@app.post("/api/analyze")
@api
def analyze():
    body = request.get_json()
    sql = ANALYZE_SQL[body["operation"]]
    return run_sql(sql, {"text": body["text"], "lang": body.get("lang", "es"),
                         "deployment": EMBEDDING_DEPLOYMENT})


# -----------------------------------------------------------------------------
# 5. Semantic operators (preview): LLM reasoning from SQL with a Foundry chat model
# -----------------------------------------------------------------------------
@app.post("/api/semantic/filter")
@api
def semantic_filter():
    """azure_ai.is_true: filter rows with a natural-language condition.
    First a cheap vector search picks candidates, then the LLM decides."""
    sql = """
        WITH q AS (
            SELECT azure_openai.create_embeddings(%(deployment)s, %(condition)s)::vector AS v
        ),
        candidates AS (
            SELECT r.id, r.hotel, r.city, r.review_text
            FROM hotel_reviews r, q
            ORDER BY r.embedding <=> q.v
            LIMIT 8
        )
        SELECT id, hotel, city, review_text
        FROM candidates
        WHERE azure_ai.is_true(
            'Hotel review: ' || review_text || ' | Statement: ' || %(condition)s,
            %(model)s
        );
    """
    body = request.get_json()
    return run_sql(sql, {"deployment": EMBEDDING_DEPLOYMENT,
                         "condition": body["condition"], "model": CHAT_DEPLOYMENT})


@app.post("/api/semantic/extract")
@api
def semantic_extract():
    """azure_ai.extract: turn free text into structured JSON."""
    sql = """
        SELECT id, hotel, review_text,
               azure_ai.extract(
                   review_text,
                   -- Each field uses the pattern 'name: type - description'
                   ARRAY[
                       'cleanliness: integer - score from 1 (dirty) to 5 (spotless)',
                       'staff_mentioned: boolean - true if the review talks about the staff',
                       'staff_name: string - name of an employee mentioned, empty if none',
                       'main_complaint: string - main complaint in Spanish, empty if none',
                       'would_return: boolean - true if the guest would likely come back'
                   ],
                   %(model)s
               ) AS extracted
        FROM hotel_reviews
        WHERE id = %(id)s;
    """
    body = request.get_json()
    return run_sql(sql, {"id": int(body["id"]), "model": CHAT_DEPLOYMENT})


@app.post("/api/semantic/ask")
@api
def semantic_ask():
    """azure_ai.generate: RAG 100%% in SQL (vector retrieval + LLM answer)."""
    sql = """
        WITH q AS (
            SELECT azure_openai.create_embeddings(%(deployment)s, %(question)s)::vector AS v
        ),
        context AS (
            SELECT string_agg(concat('[', hotel, ', ', city, '] ', review_text), chr(10)) AS docs
            FROM (
                SELECT r.hotel, r.city, r.review_text
                FROM hotel_reviews r, q
                ORDER BY r.embedding <=> q.v
                LIMIT 6
            ) AS top_reviews
        )
        SELECT azure_ai.generate(
                   'Answer in Spanish, in at most 4 sentences, using ONLY these hotel reviews. '
                   || 'Mention the hotel names.' || chr(10) || 'Reviews:' || chr(10) || docs
                   || chr(10) || 'Question: ' || %(question)s,
                   model => %(model)s
               ) AS answer,
               docs AS context_used
        FROM context;
    """
    body = request.get_json()
    return run_sql(sql, {"deployment": EMBEDDING_DEPLOYMENT,
                         "question": body["question"], "model": CHAT_DEPLOYMENT})


# -----------------------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html",
                           embedding_deployment=EMBEDDING_DEPLOYMENT,
                           chat_deployment=CHAT_DEPLOYMENT)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
