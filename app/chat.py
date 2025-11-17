"""
Chat logic module for LaserOstop CM Chatbot.

This module orchestrates the core chatbot functionality:
- RAG-enhanced context retrieval
- GPT-4o/GPT-4o-mini conversation handling
- Tunisian dialect system prompting
- Interaction logging to database

The chatbot serves as a community manager for LaserOstop Tunisia,
answering questions in Tunisian dialect (Derja) about the laser
stop-smoking process.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from openai import OpenAI

from .config import (
    OPENAI_API_KEY,
    CHAT_MODEL,
    OPENAI_TIMEOUT,
    OPENAI_MAX_RETRIES,
    DEFAULT_RAG_VERSION,
    DEFAULT_RETRIEVAL_K,
)
from .rag import retrieve_context
from .db import get_session, Interaction

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=OPENAI_TIMEOUT,
    max_retries=OPENAI_MAX_RETRIES,
)


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are the official community manager of LaserOstop Tunisia.

You answer in Tunisian dialect (Derja), mixing Arabic and French naturally when appropriate.

Your goals:
- Explain clearly the laser stop-smoking process (sessions, duration, expectations).
- Provide accurate info about address, phone number, working hours and practical details (these will be given to you in context or known instructions).
- Encourage people to book an appointment, but without pressure or harassment.
- NEVER give medical diagnosis or personalized medical advice. For health doubts, always advise them to consult their doctor or our medical specialist.
- Stay warm, respectful and professional, using a friendly social-media tone (emojis allowed but not too many).

If the user writes in French or Standard Arabic, you may answer in a mix with Tunisian dialect.
Always be concise and clear.

Key information about LaserOstop Tunisia:
- Location: Tunisia (specific address should be in retrieved context)
- Service: Laser therapy to help quit smoking (arrêt tabac par laser)
- Process: Typically 1-3 sessions, painless, stimulates acupuncture points
- Success rate: High when combined with patient motivation
- Booking: Encourage users to call or message to schedule an appointment

Remember:
- Use natural Tunisian expressions ("kifech", "chhal", "nheb", "برشا", "الآن", etc.)
- Mix Arabic script and Latin script naturally
- Be empathetic about smoking addiction
- Highlight benefits but stay realistic
- For medical concerns (pregnancy, health conditions, medications), always refer to doctor consultation
"""


# ============================================================================
# OpenAI Chat Helper
# ============================================================================

def call_gpt4o(
    messages: List[Dict[str, str]],
    model: str = CHAT_MODEL,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Call OpenAI ChatCompletion API (GPT-4o, GPT-4o-mini, GPT-5-nano).

    Args:
        messages: List of message dicts with "role" and "content" keys.
        model: Model name (e.g., "gpt-4o", "gpt-4o-mini", "gpt-5-nano-2025-08-07").
        temperature: Sampling temperature (0.0 to 2.0).
        max_tokens: Maximum tokens in response (None for model default).

    Returns:
        Assistant's response text.

    Raises:
        Exception: If API call fails after retries.
    """
    try:
        logger.debug(f"Calling {model} with {len(messages)} messages")

        # Prepare chat completion parameters
        completion_params = {
            "model": model,
            "messages": messages,
        }

        # GPT-5 models don't support temperature parameter
        if not model.startswith("gpt-5"):
            completion_params["temperature"] = temperature

        # Handle max_tokens vs max_completion_tokens
        if max_tokens:
            # GPT-5 models use max_completion_tokens
            if model.startswith("gpt-5"):
                completion_params["max_completion_tokens"] = max_tokens
            else:
                completion_params["max_tokens"] = max_tokens

        # Call OpenAI API
        response = client.chat.completions.create(**completion_params)

        # Extract assistant message
        assistant_message = response.choices[0].message.content
        logger.debug(f"Received response: {assistant_message[:100]}...")

        return assistant_message

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise


# ============================================================================
# RAG + Chat Orchestration
# ============================================================================

def build_rag_context(query: str, k: int = DEFAULT_RETRIEVAL_K) -> str:
    """
    Build RAG context block from retrieved examples.

    Args:
        query: User query for retrieval.
        k: Number of examples to retrieve.

    Returns:
        Formatted context string to include in system prompt.
    """
    results = retrieve_context(query, k=k)

    if not results:
        return ""

    context_lines = [
        f"- {result['text']} (source: {result['source']})"
        for result in results
    ]

    context_block = (
        "Here are some relevant Tunisian social media examples and knowledge snippets:\n"
        + "\n".join(context_lines)
    )

    return context_block


def chat_with_user(
    user_text: str,
    channel: str = "test",
    user_id: Optional[str] = None,
    use_rag: bool = True,
    rag_version: str = DEFAULT_RAG_VERSION,
    model_version: str = CHAT_MODEL,
    temperature: float = 0.7,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Core chatbot function: RAG retrieval + GPT-4o completion + DB logging.

    This function:
    1. Optionally retrieves relevant context using RAG
    2. Builds a conversation with system prompt and context
    3. Calls GPT-4o/GPT-4o-mini for response generation
    4. Logs the interaction to the database
    5. Returns the assistant's reply

    Args:
        user_text: User's message text.
        channel: Channel name ("whatsapp", "meta", "tiktok", "test").
        user_id: Optional user identifier.
        use_rag: Whether to use RAG for context retrieval.
        rag_version: RAG version identifier for tracking.
        model_version: OpenAI model name.
        temperature: Sampling temperature for generation.
        conversation_history: Optional previous conversation turns
                             (list of {"role": "user/assistant", "content": "..."}).

    Returns:
        Assistant's reply text.

    Raises:
        Exception: If chat generation fails.

    Example:
        >>> reply = chat_with_user(
        ...     user_text="Chhal thot les séances?",
        ...     channel="whatsapp",
        ...     user_id="212612345678",
        ... )
        >>> print(reply)
        "Les séances عندنا تقريباً 1 à 3 séances حسب الحالة..."
    """
    try:
        # Build messages list
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add RAG context if enabled
        context_block = ""
        if use_rag:
            context_block = build_rag_context(user_text, k=DEFAULT_RETRIEVAL_K)
            if context_block:
                messages.append({"role": "system", "content": context_block})
                logger.debug(f"Added RAG context ({len(context_block)} chars)")

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
            logger.debug(f"Added {len(conversation_history)} history messages")

        # Add current user message
        messages.append({"role": "user", "content": user_text})

        # Call GPT-4o
        logger.info(f"Processing message from {channel}/{user_id}: {user_text[:50]}...")
        assistant_text = call_gpt4o(
            messages=messages,
            model=model_version,
            temperature=temperature,
        )

        # Determine flags based on response content
        flags = []

        # Check for potential medical advice (basic heuristic)
        medical_keywords = ["diagnostic", "traitement", "médicament", "maladie", "علاج", "دواء"]
        if any(keyword in assistant_text.lower() for keyword in medical_keywords):
            flags.append("potential_medical_advice")

        # Check for CTA presence
        cta_keywords = ["réserver", "rendez-vous", "حجز", "موعد", "appel", "contact"]
        if any(keyword in assistant_text.lower() for keyword in cta_keywords):
            flags.append("cta_present")

        flags_str = ",".join(flags) if flags else None

        # Log interaction to database
        with get_session() as session:
            interaction = Interaction(
                user_id=user_id,
                channel=channel,
                user_text=user_text,
                assistant_text=assistant_text,
                model_version=model_version,
                rag_version=rag_version if use_rag else None,
                rag_used=use_rag,
                flags=flags_str,
                created_at=datetime.utcnow(),
            )
            session.add(interaction)

        logger.info(f"Response generated and logged: {assistant_text[:50]}...")
        return assistant_text

    except Exception as e:
        logger.error(f"Error in chat_with_user: {e}")
        # Return a graceful fallback message
        fallback_message = (
            "Désolé, j'ai un problème technique actuellement. "
            "Merci de réessayer dans quelques instants ou contactez-nous directement."
        )
        return fallback_message


# ============================================================================
# Conversation Management
# ============================================================================

def get_conversation_history(
    user_id: str,
    channel: str,
    limit: int = 5,
) -> List[Dict[str, str]]:
    """
    Retrieve recent conversation history for a user.

    Args:
        user_id: User identifier.
        channel: Channel name.
        limit: Maximum number of turns to retrieve.

    Returns:
        List of message dicts with "role" and "content" keys.
    """
    try:
        with get_session() as session:
            interactions = (
                session.query(Interaction)
                .filter(
                    Interaction.user_id == user_id,
                    Interaction.channel == channel,
                )
                .order_by(Interaction.created_at.desc())
                .limit(limit)
                .all()
            )

            # Build conversation history (reverse to chronological order)
            history = []
            for interaction in reversed(interactions):
                history.append({"role": "user", "content": interaction.user_text})
                history.append({"role": "assistant", "content": interaction.assistant_text})

            return history

    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        return []


def chat_with_history(
    user_text: str,
    channel: str,
    user_id: str,
    use_rag: bool = True,
    model_version: str = CHAT_MODEL,
    history_limit: int = 3,
) -> str:
    """
    Chat with conversation history for context-aware responses.

    Args:
        user_text: User's current message.
        channel: Channel name.
        user_id: User identifier.
        use_rag: Whether to use RAG.
        model_version: OpenAI model name.
        history_limit: Number of previous turns to include.

    Returns:
        Assistant's reply text.
    """
    # Get conversation history
    history = get_conversation_history(user_id, channel, limit=history_limit)

    # Chat with history
    return chat_with_user(
        user_text=user_text,
        channel=channel,
        user_id=user_id,
        use_rag=use_rag,
        model_version=model_version,
        conversation_history=history,
    )


# ============================================================================
# Testing Utilities
# ============================================================================

if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    print("Chat Module Test")
    print("=" * 50)

    # Test messages in different styles
    test_messages = [
        "Salam, nheb nhez rendez-vous pour arrêter de fumer",
        "Chhal thot les séances?",
        "Est-ce que le laser ça marche vraiment?",
        "أنا حامل، نجم نعمل laser؟",
        "Kifech nheb nhez rendez-vous?",
    ]

    print("\nIMPORTANT: These tests require:")
    print("1. Valid OPENAI_API_KEY in .env")
    print("2. Initialized database (run: python -m app.db)")
    print("3. Optional: Built RAG index for better context")

    print("\nExample test messages:")
    for i, msg in enumerate(test_messages, 1):
        print(f"  {i}. {msg}")

    print("\nTo run a test:")
    print('  >>> from app.chat import chat_with_user')
    print('  >>> reply = chat_with_user("Chhal thot les séances?", channel="test")')
    print('  >>> print(reply)')
