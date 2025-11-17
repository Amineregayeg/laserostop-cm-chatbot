"""
RAG (Retrieval-Augmented Generation) module for LaserOstop CM Chatbot.

This module handles:
- Vector database setup and management (using ChromaDB)
- Text embedding using multilingual sentence transformers
- Building indexes from processed Tunisian dialect datasets
- Retrieving relevant context for user queries

The module uses ChromaDB for local vector storage and
intfloat/multilingual-e5-base for multilingual embeddings
(optimized for Arabic, French, and mixed text).
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path

# Fix for SQLite version issue on Ubuntu 20.04
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import pandas as pd
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .config import (
    VECTOR_DB_DIR,
    EMBEDDING_MODEL_NAME,
    CHROMA_COLLECTION_NAME,
    DEFAULT_RETRIEVAL_K,
)

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# Global Instances (Lazy Loading)
# ============================================================================

_chroma_client: Optional[chromadb.Client] = None
_embedding_model: Optional[SentenceTransformer] = None


def get_chroma_client() -> chromadb.Client:
    """
    Get or create ChromaDB client instance (singleton pattern).

    Returns:
        chromadb.Client: Persistent ChromaDB client.
    """
    global _chroma_client

    if _chroma_client is None:
        logger.info(f"Initializing ChromaDB client at: {VECTOR_DB_DIR}")
        _chroma_client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=VECTOR_DB_DIR,
                anonymized_telemetry=False,
            )
        )
        logger.info("ChromaDB client initialized successfully")

    return _chroma_client


def get_embedding_model() -> SentenceTransformer:
    """
    Get or create embedding model instance (singleton pattern).

    Uses multilingual-e5-base which supports:
    - Arabic (including Tunisian dialect)
    - French
    - Mixed language text

    Returns:
        SentenceTransformer: Pre-trained embedding model.
    """
    global _embedding_model

    if _embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info(f"Embedding model loaded successfully (dimension: {_embedding_model.get_sentence_embedding_dimension()})")

    return _embedding_model


def get_or_create_collection(
    collection_name: str = CHROMA_COLLECTION_NAME,
    reset: bool = False,
) -> chromadb.Collection:
    """
    Get or create a ChromaDB collection.

    Args:
        collection_name: Name of the collection.
        reset: If True, delete existing collection and create new one.

    Returns:
        chromadb.Collection: The collection instance.
    """
    client = get_chroma_client()

    if reset:
        try:
            client.delete_collection(name=collection_name)
            logger.info(f"Deleted existing collection: {collection_name}")
        except Exception as e:
            logger.debug(f"No existing collection to delete: {e}")

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Tunisian dialect social media messages for LaserOstop CM"}
    )

    logger.info(f"Collection '{collection_name}' ready (count: {collection.count()})")
    return collection


# ============================================================================
# Index Building
# ============================================================================

def build_index_from_parquet(
    parquet_path: str,
    collection_name: str = CHROMA_COLLECTION_NAME,
    batch_size: int = 100,
    reset: bool = False,
) -> Dict[str, int]:
    """
    Build vector index from a Parquet file containing Tunisian dialect messages.

    Expected Parquet schema:
        - id: unique identifier (string or int)
        - text: message text (string)
        - source: data source name (string, e.g., "TUNIZI", "TSAC")
        - lang_script: language/script indicator (string, e.g., "ar", "fr", "mixed")

    Args:
        parquet_path: Path to the Parquet file.
        collection_name: Name of the ChromaDB collection.
        batch_size: Number of documents to process in each batch.
        reset: If True, reset the collection before building.

    Returns:
        Dictionary with statistics: {"total_processed": N, "total_indexed": M}

    Raises:
        FileNotFoundError: If parquet file doesn't exist.
        ValueError: If parquet schema is invalid.
    """
    parquet_file = Path(parquet_path)
    if not parquet_file.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    logger.info(f"Loading data from: {parquet_path}")
    df = pd.read_parquet(parquet_path)

    # Validate schema
    required_columns = {"id", "text", "source", "lang_script"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Remove rows with empty text
    df = df[df["text"].notna() & (df["text"].str.strip() != "")]
    total_rows = len(df)
    logger.info(f"Loaded {total_rows} valid messages")

    if total_rows == 0:
        logger.warning("No valid messages found in parquet file")
        return {"total_processed": 0, "total_indexed": 0}

    # Get or create collection
    collection = get_or_create_collection(collection_name, reset=reset)
    embedding_model = get_embedding_model()

    # Process in batches
    total_indexed = 0
    for start_idx in range(0, total_rows, batch_size):
        end_idx = min(start_idx + batch_size, total_rows)
        batch_df = df.iloc[start_idx:end_idx]

        # Prepare data
        ids = [str(row_id) for row_id in batch_df["id"].tolist()]
        texts = batch_df["text"].tolist()
        metadatas = [
            {
                "source": str(row["source"]),
                "lang_script": str(row["lang_script"]),
            }
            for _, row in batch_df.iterrows()
        ]

        # Generate embeddings
        try:
            embeddings = embedding_model.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True,
            ).tolist()

            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            total_indexed += len(ids)
            logger.info(f"Indexed batch {start_idx}-{end_idx} ({total_indexed}/{total_rows} total)")

        except Exception as e:
            logger.error(f"Error processing batch {start_idx}-{end_idx}: {e}")
            continue

    stats = {
        "total_processed": total_rows,
        "total_indexed": total_indexed,
        "collection_name": collection_name,
        "collection_total": collection.count(),
    }

    logger.info(f"Index building complete: {stats}")
    return stats


def build_index_from_texts(
    texts: List[str],
    metadatas: Optional[List[Dict]] = None,
    collection_name: str = CHROMA_COLLECTION_NAME,
    reset: bool = False,
) -> Dict[str, int]:
    """
    Build vector index from a list of texts (useful for testing or small datasets).

    Args:
        texts: List of text strings to index.
        metadatas: Optional list of metadata dicts (one per text).
        collection_name: Name of the ChromaDB collection.
        reset: If True, reset the collection before building.

    Returns:
        Dictionary with statistics.
    """
    if not texts:
        logger.warning("No texts provided to index")
        return {"total_processed": 0, "total_indexed": 0}

    collection = get_or_create_collection(collection_name, reset=reset)
    embedding_model = get_embedding_model()

    # Generate IDs
    ids = [f"doc_{i}" for i in range(len(texts))]

    # Use provided metadatas or create empty ones
    if metadatas is None:
        metadatas = [{"source": "manual"} for _ in texts]

    # Generate embeddings
    logger.info(f"Generating embeddings for {len(texts)} texts")
    embeddings = embedding_model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
    ).tolist()

    # Add to collection
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    logger.info(f"Indexed {len(texts)} texts successfully")
    return {
        "total_processed": len(texts),
        "total_indexed": len(texts),
        "collection_total": collection.count(),
    }


# ============================================================================
# Retrieval
# ============================================================================

def retrieve_context(
    query: str,
    k: int = DEFAULT_RETRIEVAL_K,
    collection_name: str = CHROMA_COLLECTION_NAME,
    filter_metadata: Optional[Dict] = None,
) -> List[Dict[str, any]]:
    """
    Retrieve relevant context for a query using vector similarity search.

    Args:
        query: User query text.
        k: Number of results to retrieve.
        collection_name: Name of the ChromaDB collection.
        filter_metadata: Optional metadata filter (e.g., {"source": "TUNIZI"}).

    Returns:
        List of dictionaries with keys:
            - text: The retrieved text
            - source: Data source
            - lang_script: Language/script indicator
            - score: Similarity score (distance, lower is better)

    Example:
        results = retrieve_context("kifech nhez rendez-vous?", k=3)
        for result in results:
            print(f"{result['text']} (score: {result['score']})")
    """
    try:
        collection = get_or_create_collection(collection_name)
        embedding_model = get_embedding_model()

        # Check if collection has any documents
        if collection.count() == 0:
            logger.warning(f"Collection '{collection_name}' is empty")
            return []

        # Generate query embedding
        query_embedding = embedding_model.encode(
            [query],
            show_progress_bar=False,
            convert_to_numpy=True,
        ).tolist()[0]

        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_metadata,
        )

        # Format results
        formatted_results = []
        if results["documents"] and len(results["documents"][0]) > 0:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "source": results["metadatas"][0][i].get("source", "unknown"),
                    "lang_script": results["metadatas"][0][i].get("lang_script", "unknown"),
                    "score": results["distances"][0][i] if "distances" in results else 0.0,
                })

        logger.debug(f"Retrieved {len(formatted_results)} results for query: {query[:50]}...")
        return formatted_results

    except Exception as e:
        logger.error(f"Error during retrieval: {e}")
        return []


def get_collection_stats(collection_name: str = CHROMA_COLLECTION_NAME) -> Dict:
    """
    Get statistics about a collection.

    Args:
        collection_name: Name of the collection.

    Returns:
        Dictionary with collection statistics.
    """
    try:
        collection = get_or_create_collection(collection_name)
        return {
            "name": collection_name,
            "count": collection.count(),
            "metadata": collection.metadata,
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {"name": collection_name, "count": 0, "error": str(e)}


# ============================================================================
# Testing Utilities
# ============================================================================

if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    print("Testing RAG module...")

    # Test with simple texts
    test_texts = [
        "Ahla, nheb nhez rendez-vous pour laser anti-tabac",
        "Chhal thot les séances?",
        "Est-ce que ça marche vraiment le laser?",
        "أنا نحب نقطع تدخين، كيفاش؟",
    ]

    print("\n1. Building test index...")
    stats = build_index_from_texts(test_texts, reset=True)
    print(f"Stats: {stats}")

    print("\n2. Testing retrieval...")
    results = retrieve_context("je veux arrêter de fumer", k=2)
    for i, result in enumerate(results):
        print(f"  {i+1}. {result['text'][:60]}... (score: {result['score']:.4f})")

    print("\n3. Collection stats:")
    print(get_collection_stats())
