"""
ASR (Automatic Speech Recognition) module for LaserOstop CM Chatbot.

This module provides audio transcription using OpenAI's Whisper API.
It handles voice messages from various platforms (WhatsApp, Meta, TikTok)
and converts them to text for processing by the chatbot.

Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
"""

import logging
from typing import Optional, BinaryIO
from io import BytesIO

from openai import OpenAI

from .config import OPENAI_API_KEY, ASR_MODEL, OPENAI_TIMEOUT

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY, timeout=OPENAI_TIMEOUT)


# ============================================================================
# Audio Transcription
# ============================================================================

def transcribe_audio(
    file_bytes: bytes,
    mime_type: str = "audio/mpeg",
    language: Optional[str] = None,
    prompt: Optional[str] = None,
) -> str:
    """
    Transcribe audio bytes to text using OpenAI Whisper API.

    Args:
        file_bytes: Audio file as bytes.
        mime_type: MIME type of the audio file. Supported types:
            - audio/mpeg (mp3)
            - audio/mp4
            - audio/wav
            - audio/webm
            - audio/m4a
        language: Optional language code (ISO-639-1, e.g., "ar" for Arabic, "fr" for French).
                 If not specified, Whisper will auto-detect.
        prompt: Optional text prompt to guide transcription style/vocabulary.
                Can include domain-specific terms like "laser", "tabac", "LaserOstop".

    Returns:
        Transcribed text as string. Returns empty string on error.

    Raises:
        ValueError: If file_bytes is empty or mime_type is invalid.

    Example:
        >>> audio_data = open("voice_message.mp3", "rb").read()
        >>> text = transcribe_audio(audio_data, mime_type="audio/mpeg", language="ar")
        >>> print(text)
        "مرحبا، نحب نقطع التدخين"
    """
    if not file_bytes:
        raise ValueError("file_bytes cannot be empty")

    # Map MIME type to file extension
    mime_to_ext = {
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/mp4": "mp4",
        "audio/wav": "wav",
        "audio/webm": "webm",
        "audio/m4a": "m4a",
        "audio/x-m4a": "m4a",
    }

    ext = mime_to_ext.get(mime_type.lower())
    if not ext:
        logger.warning(f"Unsupported MIME type: {mime_type}, defaulting to mp3")
        ext = "mp3"

    try:
        # Create a file-like object from bytes
        audio_file = BytesIO(file_bytes)
        audio_file.name = f"audio.{ext}"  # Whisper API requires a filename

        # Prepare transcription parameters
        transcription_params = {
            "model": ASR_MODEL,
            "file": audio_file,
        }

        # Add optional parameters if provided
        if language:
            transcription_params["language"] = language
        if prompt:
            transcription_params["prompt"] = prompt

        # Call Whisper API
        logger.info(f"Transcribing audio ({len(file_bytes)} bytes, {mime_type})")
        transcript = client.audio.transcriptions.create(**transcription_params)

        text = transcript.text.strip()
        logger.info(f"Transcription successful: {text[:100]}...")
        return text

    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return ""


def transcribe_audio_file(
    file_path: str,
    language: Optional[str] = None,
    prompt: Optional[str] = None,
) -> str:
    """
    Transcribe audio from a file path.

    Convenience wrapper around transcribe_audio() for file-based input.

    Args:
        file_path: Path to the audio file.
        language: Optional language code.
        prompt: Optional transcription prompt.

    Returns:
        Transcribed text as string.

    Example:
        >>> text = transcribe_audio_file("voicemail.mp3", language="ar")
    """
    import mimetypes
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Detect MIME type from file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type or not mime_type.startswith("audio/"):
        mime_type = "audio/mpeg"  # Default fallback

    # Read file bytes
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    return transcribe_audio(file_bytes, mime_type=mime_type, language=language, prompt=prompt)


# ============================================================================
# Webhook Integration Helpers
# ============================================================================

def extract_audio_from_whatsapp_webhook(webhook_data: dict) -> Optional[bytes]:
    """
    Extract audio bytes from WhatsApp webhook payload.

    This is a STUB for future implementation. The actual implementation
    will depend on the WhatsApp Business API structure.

    Args:
        webhook_data: Webhook payload from WhatsApp.

    Returns:
        Audio bytes if present, None otherwise.

    TODO: Implement actual WhatsApp webhook audio extraction:
        1. Parse webhook JSON to find audio message
        2. Extract media_id
        3. Download audio from WhatsApp API using media_id
        4. Return audio bytes
    """
    logger.warning("extract_audio_from_whatsapp_webhook is not yet implemented")
    # Placeholder structure:
    # if "messages" in webhook_data:
    #     for message in webhook_data["messages"]:
    #         if message.get("type") == "audio":
    #             media_id = message["audio"]["id"]
    #             # Download from WhatsApp API
    #             audio_bytes = download_whatsapp_media(media_id)
    #             return audio_bytes
    return None


def extract_audio_from_meta_webhook(webhook_data: dict) -> Optional[bytes]:
    """
    Extract audio bytes from Meta (Facebook/Instagram) webhook payload.

    This is a STUB for future implementation.

    Args:
        webhook_data: Webhook payload from Meta platform.

    Returns:
        Audio bytes if present, None otherwise.

    TODO: Implement actual Meta webhook audio extraction based on
    Facebook Messenger or Instagram API specifications.
    """
    logger.warning("extract_audio_from_meta_webhook is not yet implemented")
    return None


def extract_audio_from_tiktok_webhook(webhook_data: dict) -> Optional[bytes]:
    """
    Extract audio bytes from TikTok webhook payload.

    This is a STUB for future implementation.

    Args:
        webhook_data: Webhook payload from TikTok.

    Returns:
        Audio bytes if present, None otherwise.

    TODO: Implement actual TikTok webhook audio extraction based on
    TikTok Business API specifications.
    """
    logger.warning("extract_audio_from_tiktok_webhook is not yet implemented")
    return None


# ============================================================================
# Testing Utilities
# ============================================================================

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    print("ASR Module Test")
    print("=" * 50)
    print("\nThis module provides audio transcription using OpenAI Whisper.")
    print("\nSupported MIME types:")
    print("  - audio/mpeg (mp3)")
    print("  - audio/mp4")
    print("  - audio/wav")
    print("  - audio/webm")
    print("  - audio/m4a")
    print("\nExample usage:")
    print('  >>> audio_bytes = open("voice.mp3", "rb").read()')
    print('  >>> text = transcribe_audio(audio_bytes, mime_type="audio/mpeg")')
    print('  >>> print(text)')
    print("\nFor testing with actual audio, you need:")
    print("  1. A valid OPENAI_API_KEY in .env")
    print("  2. An audio file to transcribe")
