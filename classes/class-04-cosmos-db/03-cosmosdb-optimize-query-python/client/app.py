"""
Flask application for comparing vector index performance in Azure Cosmos DB.

This app demonstrates how different vector indexing strategies (flat, quantizedFlat,
diskANN) affect query performance and RU consumption. Users load 5,000 support
tickets embedded with an Azure OpenAI model, run vector similarity searches, and
compare results side-by-side.
"""
import logging
import os
from flask import Flask, render_template, request, redirect, url_for, flash

from index_functions import (
    bulk_load_documents,
    clear_all_containers,
    compare_index_performance,
    compare_filtered_performance,
    get_all_categories,
    get_all_document_counts
)
from large_dataset import load_large_dataset, LARGE_DOCUMENT_COUNT

logging.getLogger("werkzeug").setLevel(logging.WARNING)

app = Flask(__name__)
app.secret_key = os.urandom(24)


def get_sample_queries():
    """
    Get the pre-computed query vectors.

    The queries are embedded with the same Azure OpenAI model as the documents
    (text-embedding-3-small, 256 dimensions), so vector distance reflects meaning.
    They are available once the dataset has been generated (large_vectors.json).
    """
    try:
        return load_large_dataset(create_if_missing=False).get("queries", [])
    except Exception:
        return []


@app.route("/")
def index():
    """Display the main page with index comparison interface."""
    categories = get_all_categories()
    queries = get_sample_queries()
    document_counts = get_all_document_counts()

    return render_template(
        "index.html",
        categories=categories,
        queries=queries,
        document_counts=document_counts,
        large_document_count=LARGE_DOCUMENT_COUNT
    )


@app.route("/load-data", methods=["POST"])
def load_data():
    """
    Load 5,000 synthetic support tickets with real Azure OpenAI embeddings into
    all three containers.

    quantizedFlat and diskANN need roughly 1,000+ vectors before they build their
    quantized / graph structures; with fewer vectors Cosmos DB does a full scan.
    Loading the same data into the flat container lets us compare the RU cost of
    an exact (full scan) search against the other index types at this scale.
    """
    try:
        # Generates and caches the embeddings the first time (large_vectors.json)
        data = load_large_dataset()
        documents = data.get("documents", [])

        result = bulk_load_documents(documents, max_workers=20)
        total_ru = result["total_ru"]

        flash(
            f"Loaded {result['loaded_count']} of {len(documents)} documents to all containers. "
            f"RU costs - flat: {total_ru['flat']:.2f}, "
            f"quantizedFlat: {total_ru['quantizedFlat']:.2f}, "
            f"diskANN: {total_ru['diskANN']:.2f}",
            "success"
        )
    except Exception as e:
        flash(f"Error loading data: {str(e)}", "error")

    return redirect(url_for("index"))


@app.route("/clear-data", methods=["POST"])
def clear_data():
    """Delete all documents from the three containers (the containers are kept)."""
    try:
        deleted = clear_all_containers()
        flash(
            f"Deleted documents - flat: {deleted['flat']}, "
            f"quantizedFlat: {deleted['quantizedFlat']}, diskANN: {deleted['diskANN']}",
            "success"
        )
    except Exception as e:
        flash(f"Error deleting data: {str(e)}", "error")

    return redirect(url_for("index"))


@app.route("/compare-search", methods=["POST"])
def compare_search():
    """Run vector similarity search against all containers and compare results."""
    query_id = request.form.get("query_id", "").strip()
    top_n = int(request.form.get("top_n", 5))

    if not query_id:
        flash("Please select a query", "error")
        return redirect(url_for("index"))

    try:
        # Get the query embedding from sample data
        queries = get_sample_queries()
        query = next((q for q in queries if q["id"] == query_id), None)

        if not query:
            flash("Query not found", "error")
            return redirect(url_for("index"))

        # Run comparison across all three containers
        comparison = compare_index_performance(query["embedding"], top_n)

        categories = get_all_categories()
        all_queries = get_sample_queries()
        document_counts = get_all_document_counts()

        return render_template(
            "index.html",
            categories=categories,
            queries=all_queries,
            document_counts=document_counts,
            comparison_result=comparison,
            comparison_query=query["description"],
            comparison_top_n=top_n
        )
    except Exception as e:
        flash(f"Error performing comparison: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/compare-filtered", methods=["POST"])
def compare_filtered():
    """Run filtered vector search against all containers and compare."""
    query_id = request.form.get("filtered_query_id", "").strip()
    category = request.form.get("filter_category", "").strip()
    top_n = int(request.form.get("filtered_top_n", 5))

    if not query_id:
        flash("Please select a query", "error")
        return redirect(url_for("index"))

    try:
        queries = get_sample_queries()
        query = next((q for q in queries if q["id"] == query_id), None)

        if not query:
            flash("Query not found", "error")
            return redirect(url_for("index"))

        # Run filtered comparison across all containers
        comparison = compare_filtered_performance(
            query["embedding"],
            category=category if category else None,
            top_n=top_n
        )

        categories = get_all_categories()
        all_queries = get_sample_queries()
        document_counts = get_all_document_counts()

        return render_template(
            "index.html",
            categories=categories,
            queries=all_queries,
            document_counts=document_counts,
            filtered_result=comparison,
            filtered_query=query["description"],
            filtered_category=category,
            filtered_top_n=top_n
        )
    except Exception as e:
        flash(f"Error performing filtered comparison: {str(e)}", "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    # Local-only dashboard
    print("Dashboard running at http://127.0.0.1:5000", flush=True)
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
