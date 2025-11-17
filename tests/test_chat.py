"""
Tests for chat module.

Tests cover:
- Chat message handling
- RAG integration
- Database logging
- Conversation history
- Error handling
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.chat import (
    chat_with_user,
    build_rag_context,
    get_conversation_history,
    SYSTEM_PROMPT,
)
from app.db import get_session, Interaction, init_db


class TestChatModule:
    """Test suite for chat module."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Initialize database before each test."""
        init_db()

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response."""
        return "Ahla! Ena nhebek bech nhez rendez-vous. Tsalli 3al [phone] w net3arfou 3lik."

    def test_system_prompt_structure(self):
        """Test that system prompt is properly structured."""
        assert "LaserOstop Tunisia" in SYSTEM_PROMPT
        assert "Tunisian dialect" in SYSTEM_PROMPT
        assert "Derja" in SYSTEM_PROMPT
        assert "medical" in SYSTEM_PROMPT.lower()

    @patch("app.chat.client.chat.completions.create")
    def test_chat_with_user_basic(self, mock_create, mock_openai_response):
        """Test basic chat interaction."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = mock_openai_response
        mock_create.return_value = mock_response

        # Call chat
        reply = chat_with_user(
            user_text="Nheb nhez rendez-vous",
            channel="test",
            use_rag=False,
        )

        assert reply == mock_openai_response
        mock_create.assert_called_once()

    @patch("app.chat.client.chat.completions.create")
    def test_chat_logs_to_database(self, mock_create, mock_openai_response):
        """Test that interactions are logged to database."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = mock_openai_response
        mock_create.return_value = mock_response

        user_text = "Test message"
        user_id = "test_user_123"

        # Call chat
        chat_with_user(
            user_text=user_text,
            channel="test",
            user_id=user_id,
            use_rag=False,
        )

        # Check database
        with get_session() as session:
            interaction = (
                session.query(Interaction)
                .filter(Interaction.user_id == user_id)
                .first()
            )

            assert interaction is not None
            assert interaction.user_text == user_text
            assert interaction.assistant_text == mock_openai_response
            assert interaction.channel == "test"
            assert interaction.rag_used is False

    @patch("app.chat.client.chat.completions.create")
    @patch("app.chat.retrieve_context")
    def test_chat_with_rag(self, mock_retrieve, mock_create, mock_openai_response):
        """Test chat with RAG enabled."""
        # Mock RAG retrieval
        mock_retrieve.return_value = [
            {"text": "Example 1", "source": "test", "score": 0.8},
            {"text": "Example 2", "source": "test", "score": 0.7},
        ]

        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = mock_openai_response
        mock_create.return_value = mock_response

        # Call chat with RAG
        reply = chat_with_user(
            user_text="Chhal thot les séances?",
            channel="test",
            use_rag=True,
        )

        # Verify RAG was called
        mock_retrieve.assert_called_once()
        assert reply == mock_openai_response

    @patch("app.chat.client.chat.completions.create")
    def test_chat_with_conversation_history(self, mock_create, mock_openai_response):
        """Test chat with conversation history."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = mock_openai_response
        mock_create.return_value = mock_response

        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]

        reply = chat_with_user(
            user_text="Follow-up question",
            channel="test",
            use_rag=False,
            conversation_history=history,
        )

        assert reply == mock_openai_response

        # Check that history was included in API call
        call_args = mock_create.call_args
        messages = call_args.kwargs["messages"]

        # Should have: system prompt + history + current message
        assert len(messages) >= 3

    def test_build_rag_context_empty(self):
        """Test RAG context building with no results."""
        with patch("app.chat.retrieve_context") as mock_retrieve:
            mock_retrieve.return_value = []

            context = build_rag_context("test query", k=5)
            assert context == ""

    def test_build_rag_context_with_results(self):
        """Test RAG context building with results."""
        with patch("app.chat.retrieve_context") as mock_retrieve:
            mock_retrieve.return_value = [
                {"text": "Example 1", "source": "test1", "score": 0.9},
                {"text": "Example 2", "source": "test2", "score": 0.8},
            ]

            context = build_rag_context("test query", k=2)

            assert "Example 1" in context
            assert "Example 2" in context
            assert "source" in context.lower()

    @patch("app.chat.client.chat.completions.create")
    def test_chat_with_different_channels(self, mock_create, mock_openai_response):
        """Test chat with different channel types."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = mock_openai_response
        mock_create.return_value = mock_response

        channels = ["whatsapp", "meta", "tiktok", "test"]

        for channel in channels:
            reply = chat_with_user(
                user_text=f"Test from {channel}",
                channel=channel,
                user_id=f"user_{channel}",
                use_rag=False,
            )

            assert reply == mock_openai_response

            # Verify channel was logged
            with get_session() as session:
                interaction = (
                    session.query(Interaction)
                    .filter(Interaction.channel == channel)
                    .first()
                )
                assert interaction is not None

    @patch("app.chat.client.chat.completions.create")
    def test_chat_error_handling(self, mock_create):
        """Test chat error handling."""
        # Mock API error
        mock_create.side_effect = Exception("API Error")

        reply = chat_with_user(
            user_text="Test message",
            channel="test",
            use_rag=False,
        )

        # Should return fallback message
        assert "problème technique" in reply.lower() or "error" in reply.lower()

    @patch("app.chat.client.chat.completions.create")
    def test_get_conversation_history(self, mock_create, mock_openai_response):
        """Test retrieving conversation history."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = mock_openai_response
        mock_create.return_value = mock_response

        user_id = "history_test_user"
        channel = "test"

        # Create some interactions
        for i in range(3):
            chat_with_user(
                user_text=f"Message {i}",
                channel=channel,
                user_id=user_id,
                use_rag=False,
            )

        # Get history
        history = get_conversation_history(user_id, channel, limit=5)

        # Should have alternating user/assistant messages
        assert len(history) == 6  # 3 user + 3 assistant
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"


class TestChatFlags:
    """Test chat flag detection."""

    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Initialize database before each test."""
        init_db()

    @patch("app.chat.client.chat.completions.create")
    def test_cta_flag_detection(self, mock_create):
        """Test CTA (call-to-action) flag detection."""
        # Mock response with CTA
        response_with_cta = "Nhebou nhez rendez-vous pour esmaa3 akthar. Tsalli 3al [phone]!"
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = response_with_cta
        mock_create.return_value = mock_response

        chat_with_user(
            user_text="Test",
            channel="test",
            user_id="cta_test",
            use_rag=False,
        )

        # Check flags in database
        with get_session() as session:
            interaction = (
                session.query(Interaction)
                .filter(Interaction.user_id == "cta_test")
                .first()
            )

            assert interaction.flags is not None
            assert "cta_present" in interaction.flags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
