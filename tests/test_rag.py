"""
Tests for RAG module.

Tests cover:
- Vector index building from texts
- Embedding generation
- Context retrieval
- Collection management
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag import (
    build_index_from_texts,
    retrieve_context,
    get_collection_stats,
    get_or_create_collection,
)


class TestRAGModule:
    """Test suite for RAG module."""

    @pytest.fixture
    def sample_texts(self):
        """Sample Tunisian dialect texts for testing."""
        return [
            "Ahla, nheb nhez rendez-vous pour laser anti-tabac",
            "Chhal thot les séances?",
            "Est-ce que ça marche vraiment le laser?",
            "أنا نحب نقطع تدخين، كيفاش؟",
            "Je veux arrêter de fumer, comment faire?",
        ]

    @pytest.fixture
    def sample_metadatas(self):
        """Sample metadata for texts."""
        return [
            {"source": "test", "lang_script": "mixed"},
            {"source": "test", "lang_script": "fr"},
            {"source": "test", "lang_script": "fr"},
            {"source": "test", "lang_script": "ar"},
            {"source": "test", "lang_script": "fr"},
        ]

    def test_build_index_from_texts_basic(self, sample_texts):
        """Test building index from a list of texts."""
        stats = build_index_from_texts(
            texts=sample_texts,
            collection_name="test_collection",
            reset=True,
        )

        assert stats["total_processed"] == len(sample_texts)
        assert stats["total_indexed"] == len(sample_texts)
        assert stats["collection_total"] >= len(sample_texts)

    def test_build_index_from_texts_with_metadata(self, sample_texts, sample_metadatas):
        """Test building index with metadata."""
        stats = build_index_from_texts(
            texts=sample_texts,
            metadatas=sample_metadatas,
            collection_name="test_collection_metadata",
            reset=True,
        )

        assert stats["total_processed"] == len(sample_texts)
        assert stats["total_indexed"] == len(sample_texts)

    def test_build_index_empty_texts(self):
        """Test building index with empty text list."""
        stats = build_index_from_texts(
            texts=[],
            collection_name="test_empty",
            reset=True,
        )

        assert stats["total_processed"] == 0
        assert stats["total_indexed"] == 0

    def test_retrieve_context_basic(self, sample_texts):
        """Test retrieving context from index."""
        # Build index first
        build_index_from_texts(
            texts=sample_texts,
            collection_name="test_retrieval",
            reset=True,
        )

        # Retrieve context
        results = retrieve_context(
            query="je veux arrêter de fumer",
            k=3,
            collection_name="test_retrieval",
        )

        assert len(results) <= 3
        assert all("text" in r for r in results)
        assert all("source" in r for r in results)
        assert all("score" in r for r in results)

    def test_retrieve_context_empty_collection(self):
        """Test retrieval from empty collection."""
        # Create empty collection
        get_or_create_collection("test_empty_retrieval", reset=True)

        results = retrieve_context(
            query="test query",
            k=5,
            collection_name="test_empty_retrieval",
        )

        assert results == []

    def test_retrieve_context_with_filter(self, sample_texts, sample_metadatas):
        """Test retrieval with metadata filter."""
        # Build index with metadata
        build_index_from_texts(
            texts=sample_texts,
            metadatas=sample_metadatas,
            collection_name="test_filter",
            reset=True,
        )

        # Retrieve with filter
        results = retrieve_context(
            query="arrêter de fumer",
            k=5,
            collection_name="test_filter",
            filter_metadata={"source": "test"},
        )

        assert all(r["source"] == "test" for r in results)

    def test_get_collection_stats(self, sample_texts):
        """Test getting collection statistics."""
        collection_name = "test_stats"

        # Build index
        build_index_from_texts(
            texts=sample_texts,
            collection_name=collection_name,
            reset=True,
        )

        # Get stats
        stats = get_collection_stats(collection_name)

        assert "name" in stats
        assert "count" in stats
        assert stats["name"] == collection_name
        assert stats["count"] == len(sample_texts)

    def test_multilingual_retrieval(self):
        """Test retrieval with multilingual queries."""
        texts = [
            "Bonjour, je veux arrêter de fumer",
            "مرحبا، أنا نحب نقطع التدخين",
            "Ahla, nheb naqta3 tabac",
        ]

        build_index_from_texts(
            texts=texts,
            collection_name="test_multilingual",
            reset=True,
        )

        # Test different language queries
        queries = [
            "comment arrêter tabac",
            "كيفاش نقطع التدخين",
            "kifech naqta3 smoking",
        ]

        for query in queries:
            results = retrieve_context(
                query=query,
                k=2,
                collection_name="test_multilingual",
            )
            assert len(results) > 0


class TestRAGEdgeCases:
    """Test edge cases and error handling."""

    def test_retrieve_with_special_characters(self):
        """Test retrieval with special characters in query."""
        texts = ["Normal text", "Text with émojis 😊", "Texte spécial: @#$%"]

        build_index_from_texts(
            texts=texts,
            collection_name="test_special",
            reset=True,
        )

        results = retrieve_context(
            query="émojis @#$",
            k=2,
            collection_name="test_special",
        )

        assert isinstance(results, list)

    def test_very_long_text(self):
        """Test indexing very long text."""
        long_text = "word " * 1000  # 1000 words

        stats = build_index_from_texts(
            texts=[long_text],
            collection_name="test_long",
            reset=True,
        )

        assert stats["total_indexed"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
