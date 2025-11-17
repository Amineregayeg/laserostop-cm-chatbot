"""
Configuration module for LaserOstop CM Chatbot.

This module loads environment variables and exposes configuration
settings for the entire application.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in environment variables.", file=sys.stderr)
    print("Please copy .env.example to .env and set your OpenAI API key.", file=sys.stderr)
    sys.exit(1)

# Database Configuration
DB_URL = os.getenv("DB_URL", "sqlite:///laserostop_cm.db")

# Vector Store Configuration
VECTOR_DB_DIR = os.getenv("VECTOR_DB_DIR", "./vector_store")
Path(VECTOR_DB_DIR).mkdir(parents=True, exist_ok=True)

# Embedding Model Configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

# LLM Model Configuration
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")  # Can upgrade to "gpt-4o" for better quality
ASR_MODEL = os.getenv("ASR_MODEL", "whisper-1")

# Flask Configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

# OpenAI Client Configuration
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))

# Data Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EVAL_SETS_DIR = DATA_DIR / "eval_sets"

# Ensure data directories exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EVAL_SETS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# RAG Configuration
DEFAULT_RAG_VERSION = "rag_v1"
DEFAULT_RETRIEVAL_K = 5  # Number of context examples to retrieve
CHROMA_COLLECTION_NAME = "laserostop_tunisian_messages"

# Evaluation Configuration
DEFAULT_EVAL_BATCH_SIZE = 100
