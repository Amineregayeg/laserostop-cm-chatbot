#!/usr/bin/env python3
"""
Build RAG index script for LaserOstop CM Chatbot.

This script builds the vector index from processed Tunisian dialect datasets.
It loads data from data/processed/messages.parquet and creates a ChromaDB
vector index for RAG retrieval.

Usage:
    python scripts/build_index.py [--reset] [--input PATH]

Arguments:
    --reset: Reset existing index before building
    --input: Path to parquet file (default: data/processed/messages.parquet)
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag import build_index_from_parquet, get_collection_stats
from app.config import PROCESSED_DATA_DIR, CHROMA_COLLECTION_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Main function to build RAG index."""
    parser = argparse.ArgumentParser(
        description="Build RAG vector index from Tunisian dialect datasets"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset existing index before building",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(PROCESSED_DATA_DIR / "messages.parquet"),
        help="Path to input parquet file (default: data/processed/messages.parquet)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for indexing (default: 100)",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("LaserOstop CM - RAG Index Builder")
    logger.info("=" * 60)

    # Check if input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("\nPlease ensure you have:")
        logger.info("  1. Prepared your Tunisian dialect datasets")
        logger.info("  2. Saved them as a Parquet file with columns:")
        logger.info("     - id: unique identifier")
        logger.info("     - text: message text")
        logger.info("     - source: data source (e.g., TUNIZI, TSAC)")
        logger.info("     - lang_script: language/script (e.g., ar, fr, mixed)")
        logger.info(f"  3. Placed the file at: {input_path}")
        sys.exit(1)

    # Get initial collection stats
    logger.info("\nInitial collection status:")
    initial_stats = get_collection_stats(CHROMA_COLLECTION_NAME)
    logger.info(f"  Collection: {initial_stats['name']}")
    logger.info(f"  Current count: {initial_stats['count']}")

    # Build index
    logger.info(f"\nBuilding index from: {input_path}")
    logger.info(f"Reset mode: {args.reset}")
    logger.info(f"Batch size: {args.batch_size}")

    try:
        stats = build_index_from_parquet(
            parquet_path=str(input_path),
            collection_name=CHROMA_COLLECTION_NAME,
            batch_size=args.batch_size,
            reset=args.reset,
        )

        logger.info("\n" + "=" * 60)
        logger.info("Index building completed successfully!")
        logger.info("=" * 60)
        logger.info(f"Total processed: {stats['total_processed']}")
        logger.info(f"Total indexed: {stats['total_indexed']}")
        logger.info(f"Collection total: {stats['collection_total']}")

        # Get final collection stats
        logger.info("\nFinal collection status:")
        final_stats = get_collection_stats(CHROMA_COLLECTION_NAME)
        logger.info(f"  Collection: {final_stats['name']}")
        logger.info(f"  Total documents: {final_stats['count']}")

        logger.info("\nNext steps:")
        logger.info("  1. Test retrieval: python -m app.rag")
        logger.info("  2. Start Flask app: python -m app")
        logger.info("  3. Test chat endpoint: curl -X POST http://localhost:5000/chat")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error building index: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
