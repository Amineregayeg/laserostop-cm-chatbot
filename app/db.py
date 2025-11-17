"""
Database module for LaserOstop CM Chatbot.

This module defines SQLAlchemy models for:
- Interactions: User conversations with the chatbot
- EvalExample: Gold standard evaluation examples
- EvalRun: Batch evaluation runs
- EvalResult: Individual evaluation results

It also provides database session management and initialization.
"""

from datetime import datetime
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .config import DB_URL

# Create engine with appropriate settings
# For SQLite, use check_same_thread=False to allow multi-threaded access
engine_kwargs = {}
if DB_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    # Use StaticPool for in-memory databases, otherwise use default
    if ":memory:" in DB_URL:
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DB_URL, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


# ============================================================================
# Models
# ============================================================================

class Interaction(Base):
    """
    Stores user interactions with the chatbot.

    This table logs every conversation turn, including:
    - User input and bot response
    - Channel information (WhatsApp, Meta, TikTok, etc.)
    - Model and RAG version used
    - Flags for special handling (escalation, low confidence, etc.)
    """
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    channel = Column(String, nullable=True, index=True)  # "whatsapp", "meta", "tiktok", "test"

    user_text = Column(Text, nullable=False)
    assistant_text = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Model tracking
    model_version = Column(String, nullable=False, index=True)  # e.g., "gpt-4o", "gpt-4o-mini"
    rag_version = Column(String, nullable=True, index=True)     # e.g., "rag_v1", "rag_v2"
    rag_used = Column(Boolean, default=True, nullable=False)

    # Special flags (comma-separated or JSON string)
    # Examples: "escalated_to_human", "low_conf", "medical_risk_detected"
    flags = Column(String, nullable=True)

    def __repr__(self):
        return f"<Interaction(id={self.id}, user_id={self.user_id}, channel={self.channel}, created_at={self.created_at})>"


class EvalExample(Base):
    """
    Gold standard evaluation examples.

    These are manually curated or high-quality examples used to evaluate
    chatbot performance. Each example may have:
    - An input text (required)
    - An ideal/expected answer (optional, for accuracy metrics)
    - Category labels (e.g., "price", "booking", "contraindication")
    - Sensitivity flags (e.g., "medical_risk", "normal")
    """
    __tablename__ = "eval_examples"

    id = Column(Integer, primary_key=True, index=True)

    input_text = Column(Text, nullable=False)
    ideal_answer = Column(Text, nullable=True)  # Nullable for rating-only evaluation

    # Categorization
    category = Column(String, nullable=True, index=True)  # e.g., "price", "booking", "contraindication"
    sensitivity = Column(String, nullable=True, index=True)  # e.g., "normal", "medical_risk"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<EvalExample(id={self.id}, category={self.category}, sensitivity={self.sensitivity})>"


class EvalRun(Base):
    """
    Batch evaluation run metadata.

    Each evaluation run tests the chatbot against a set of EvalExamples
    and computes aggregate metrics:
    - Accuracy score (how many answers were acceptable)
    - Dialect score (quality of Tunisian dialect usage)
    - Safety score (avoiding medical advice, inappropriate content)
    - CTA presence rate (call-to-action inclusion)
    """
    __tablename__ = "eval_runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Model configuration
    model_version = Column(String, nullable=False, index=True)
    rag_version = Column(String, nullable=True, index=True)

    # Aggregate metrics
    num_examples = Column(Integer, nullable=False)
    accuracy_score = Column(Float, nullable=True)      # 0.0 to 1.0
    dialect_score = Column(Float, nullable=True)        # 0.0 to 1.0 (manual annotation)
    safety_score = Column(Float, nullable=True)         # 0.0 to 1.0 (manual annotation)
    cta_presence_rate = Column(Float, nullable=True)    # 0.0 to 1.0

    # Additional notes or metadata
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<EvalRun(id={self.id}, model={self.model_version}, examples={self.num_examples}, accuracy={self.accuracy_score})>"


class EvalResult(Base):
    """
    Individual evaluation result for a single example.

    Links an EvalRun to an EvalExample and stores:
    - The input and ideal answer
    - The predicted answer from the model
    - Whether the answer was acceptable
    - Error type if the answer failed
    """
    __tablename__ = "eval_results"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    eval_run_id = Column(Integer, ForeignKey("eval_runs.id"), nullable=False, index=True)
    eval_example_id = Column(Integer, ForeignKey("eval_examples.id"), nullable=False, index=True)

    # Data snapshot (denormalized for easy access)
    input_text = Column(Text, nullable=False)
    ideal_answer = Column(Text, nullable=True)
    predicted_answer = Column(Text, nullable=False)

    # Evaluation outcome
    is_acceptable = Column(Boolean, nullable=True)  # None if not evaluated yet
    error_type = Column(String, nullable=True)  # e.g., "wrong_price", "missing_cta", "medical_risk"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<EvalResult(id={self.id}, run_id={self.eval_run_id}, acceptable={self.is_acceptable})>"


# ============================================================================
# Session Management
# ============================================================================

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Usage:
        with get_session() as session:
            session.add(obj)
            session.commit()

    Automatically handles cleanup and rollback on errors.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Session:
    """
    Get a new database session.

    Note: Caller is responsible for closing the session.
    Prefer using get_session() context manager when possible.
    """
    return SessionLocal()


# ============================================================================
# Database Initialization
# ============================================================================

def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This is idempotent - safe to call multiple times.
    """
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized successfully at: {DB_URL}")


def drop_all_tables() -> None:
    """
    Drop all tables from the database.

    WARNING: This will delete all data! Use with caution.
    Primarily for testing and development.
    """
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped successfully.")


# ============================================================================
# Utility Functions
# ============================================================================

def get_table_counts() -> dict:
    """
    Get row counts for all tables.

    Returns:
        Dictionary mapping table names to row counts.
    """
    with get_session() as session:
        return {
            "interactions": session.query(Interaction).count(),
            "eval_examples": session.query(EvalExample).count(),
            "eval_runs": session.query(EvalRun).count(),
            "eval_results": session.query(EvalResult).count(),
        }


if __name__ == "__main__":
    # Allow running this module directly to initialize the database
    print("Initializing database...")
    init_db()
    counts = get_table_counts()
    print(f"Table counts: {counts}")
