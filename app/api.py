"""
API routes for LaserOstop CM Chatbot.

This module defines Flask routes for:
- Health check endpoint
- Chat endpoint (main conversational interface)
- Webhook stubs for WhatsApp, Meta (FB/IG), and TikTok
"""

import logging
from typing import Dict, Any
from flask import Flask, request, jsonify

from .chat import chat_with_user, chat_with_history
from .asr import transcribe_audio
from .config import CHAT_MODEL, DEFAULT_RAG_VERSION

logger = logging.getLogger(__name__)


# ============================================================================
# Route Registration
# ============================================================================

def register_routes(app: Flask) -> None:
    """
    Register all API routes with the Flask app.

    Args:
        app: Flask application instance.
    """

    # ========================================================================
    # Health Check
    # ========================================================================

    @app.route("/health", methods=["GET"])
    def health():
        """
        Health check endpoint.

        Returns:
            JSON with status "ok".
        """
        return jsonify({"status": "ok"}), 200

    # ========================================================================
    # Chat Endpoint
    # ========================================================================

    @app.route("/chat", methods=["POST"])
    def chat():
        """
        Main chat endpoint for conversational interface.

        Request JSON:
            {
                "text": "user message here",
                "user_id": "optional-user-id",
                "channel": "whatsapp|meta|tiktok|test",
                "use_rag": true,
                "model_version": "gpt-4o-mini",
                "use_history": false
            }

        Response JSON:
            {
                "reply": "assistant reply text",
                "model_version": "gpt-4o-mini",
                "rag_used": true,
                "rag_version": "rag_v1"
            }

        Returns:
            JSON response with chatbot reply.
        """
        try:
            # Parse request JSON
            data = request.get_json()

            if not data:
                return jsonify({"error": "Request body must be JSON"}), 400

            # Extract required field
            user_text = data.get("text")
            if not user_text:
                return jsonify({"error": "Field 'text' is required"}), 400

            # Extract optional fields
            user_id = data.get("user_id")
            channel = data.get("channel", "test")
            use_rag = data.get("use_rag", True)
            model_version = data.get("model_version", CHAT_MODEL)
            use_history = data.get("use_history", False)

            # Call chat function (with or without history)
            if use_history and user_id:
                reply = chat_with_history(
                    user_text=user_text,
                    channel=channel,
                    user_id=user_id,
                    use_rag=use_rag,
                    model_version=model_version,
                )
            else:
                reply = chat_with_user(
                    user_text=user_text,
                    channel=channel,
                    user_id=user_id,
                    use_rag=use_rag,
                    model_version=model_version,
                )

            # Build response
            response = {
                "reply": reply,
                "model_version": model_version,
                "rag_used": use_rag,
                "rag_version": DEFAULT_RAG_VERSION if use_rag else None,
            }

            logger.info(f"Chat request processed: {user_text[:50]}...")
            return jsonify(response), 200

        except Exception as e:
            logger.error(f"Error in /chat endpoint: {e}")
            return jsonify({"error": "Internal server error", "details": str(e)}), 500

    # ========================================================================
    # Webhook Stubs
    # ========================================================================

    @app.route("/webhook/whatsapp", methods=["GET", "POST"])
    def webhook_whatsapp():
        """
        WhatsApp webhook endpoint (stub for future implementation).

        GET: Webhook verification (WhatsApp requires this)
        POST: Incoming message handling

        TODO: Implement full WhatsApp Business API integration:
        1. Verify webhook on GET requests (verify_token)
        2. Parse incoming messages (text, audio, etc.)
        3. Extract message content and user info
        4. Call chat_with_user() or transcribe_audio() + chat
        5. Send reply via WhatsApp API

        Resources:
        - WhatsApp Business API docs: https://developers.facebook.com/docs/whatsapp
        - Webhook setup guide
        """
        if request.method == "GET":
            # Webhook verification
            verify_token = request.args.get("hub.verify_token")
            challenge = request.args.get("hub.challenge")

            # TODO: Check verify_token against configured secret
            # For now, just return challenge for testing
            if challenge:
                logger.info("WhatsApp webhook verification request")
                return challenge, 200

            return jsonify({"error": "Invalid verification request"}), 400

        elif request.method == "POST":
            # Incoming message
            data = request.get_json()
            logger.info(f"WhatsApp webhook received: {data}")

            # TODO: Parse WhatsApp webhook payload
            # Example structure:
            # {
            #   "messages": [{
            #     "from": "212612345678",
            #     "type": "text",
            #     "text": {"body": "user message"}
            #   }]
            # }

            # Stub response
            return jsonify({"status": "received"}), 200

    @app.route("/webhook/meta", methods=["GET", "POST"])
    def webhook_meta():
        """
        Meta (Facebook/Instagram) webhook endpoint (stub for future implementation).

        TODO: Implement Meta Messenger/Instagram integration:
        1. Handle webhook verification
        2. Parse messaging events (text, audio, images)
        3. Extract sender PSID and message content
        4. Call chat_with_user()
        5. Send reply via Send API

        Resources:
        - Messenger Platform docs: https://developers.facebook.com/docs/messenger-platform
        - Instagram Messaging API
        """
        if request.method == "GET":
            # Webhook verification
            verify_token = request.args.get("hub.verify_token")
            challenge = request.args.get("hub.challenge")

            if challenge:
                logger.info("Meta webhook verification request")
                return challenge, 200

            return jsonify({"error": "Invalid verification request"}), 400

        elif request.method == "POST":
            # Incoming message
            data = request.get_json()
            logger.info(f"Meta webhook received: {data}")

            # TODO: Parse Meta webhook payload
            # Example structure (Messenger):
            # {
            #   "entry": [{
            #     "messaging": [{
            #       "sender": {"id": "1234567890"},
            #       "message": {"text": "user message"}
            #     }]
            #   }]
            # }

            # Stub response
            return jsonify({"status": "received"}), 200

    @app.route("/webhook/tiktok", methods=["POST"])
    def webhook_tiktok():
        """
        TikTok webhook endpoint (stub for future implementation).

        TODO: Implement TikTok Business integration:
        1. Handle TikTok webhook authentication
        2. Parse incoming messages and comments
        3. Extract user info and message content
        4. Call chat_with_user()
        5. Reply via TikTok API

        Resources:
        - TikTok for Business API docs
        - TikTok Messaging API (if available)
        """
        data = request.get_json()
        logger.info(f"TikTok webhook received: {data}")

        # TODO: Parse TikTok webhook payload
        # Structure depends on TikTok's API specification

        # Stub response
        return jsonify({"status": "received"}), 200

    # ========================================================================
    # Utility Endpoints (optional, for debugging/monitoring)
    # ========================================================================

    @app.route("/stats", methods=["GET"])
    def stats():
        """
        Get database and system statistics.

        Returns:
            JSON with table counts and system info.
        """
        from .db import get_table_counts
        from .rag import get_collection_stats

        try:
            db_stats = get_table_counts()
            rag_stats = get_collection_stats()

            return jsonify({
                "database": db_stats,
                "rag": rag_stats,
            }), 200

        except Exception as e:
            logger.error(f"Error in /stats endpoint: {e}")
            return jsonify({"error": str(e)}), 500

    logger.info("API routes registered successfully")


# ============================================================================
# Error Handlers
# ============================================================================

def register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers.

    Args:
        app: Flask application instance.
    """

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({"error": "Internal server error"}), 500
