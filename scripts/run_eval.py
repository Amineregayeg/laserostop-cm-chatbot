#!/usr/bin/env python3
"""
Evaluation runner script for LaserOstop CM Chatbot.

This script runs offline evaluation on the EvalExample dataset
and stores results in the database.

Usage:
    python scripts/run_eval.py [OPTIONS]

Examples:
    # Evaluate gpt-4o-mini with RAG on 100 examples
    python scripts/run_eval.py --model gpt-4o-mini --rag-version rag_v1 --limit 100

    # Evaluate without RAG
    python scripts/run_eval.py --model gpt-4o-mini --no-rag --limit 50

    # Evaluate specific category
    python scripts/run_eval.py --category booking --limit 20
"""

import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.eval import run_evaluation, get_eval_run_summary
from app.config import CHAT_MODEL, DEFAULT_RAG_VERSION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def print_summary(summary: dict) -> None:
    """
    Print evaluation summary in a readable format.

    Args:
        summary: Evaluation summary dictionary.
    """
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    if "error" in summary:
        print(f"ERROR: {summary['error']}")
        return

    print(f"Eval Run ID: {summary['eval_run_id']}")
    print(f"Model: {summary['model_version']}")
    print(f"RAG Version: {summary['rag_version'] or 'N/A'}")
    print(f"Total Examples: {summary['num_examples']}")
    print(f"Examples with Labels: {summary['num_with_labels']}")

    print("\n" + "-" * 70)
    print("METRICS")
    print("-" * 70)

    # Accuracy
    if summary['accuracy_score'] is not None:
        accuracy_pct = summary['accuracy_score'] * 100
        print(f"Accuracy: {accuracy_pct:.1f}% ({summary['num_with_labels']} examples)")
    else:
        print("Accuracy: N/A (no labeled examples)")

    # CTA presence
    cta_pct = summary['cta_presence_rate'] * 100
    print(f"CTA Presence: {cta_pct:.1f}%")

    # Safety
    safety_pct = summary['safety_score'] * 100
    print(f"Safety Score: {safety_pct:.1f}% ({summary['num_unsafe']} unsafe)")

    print("\n" + "-" * 70)
    print("ERROR BREAKDOWN")
    print("-" * 70)

    # Count error types
    error_counts = {}
    for result in summary['results']:
        if result['error_type']:
            error_type = result['error_type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

    if error_counts:
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / summary['num_examples']) * 100
            print(f"  {error_type}: {count} ({pct:.1f}%)")
    else:
        print("  No errors detected")

    print("\n" + "=" * 70)


def save_results_to_file(summary: dict, output_path: str) -> None:
    """
    Save evaluation results to a JSON file.

    Args:
        summary: Evaluation summary dictionary.
        output_path: Path to save JSON file.
    """
    # Remove results list from summary for cleaner overview file
    summary_overview = {k: v for k, v in summary.items() if k != 'results'}

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary_overview, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to: {output_path}")

    # Also save detailed results
    detailed_path = output_path.replace('.json', '_detailed.json')
    with open(detailed_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"Detailed results saved to: {detailed_path}")


def main():
    """Main function to run evaluation."""
    parser = argparse.ArgumentParser(
        description="Run evaluation on LaserOstop CM Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic evaluation with default settings
  python scripts/run_eval.py --limit 50

  # Evaluate specific model and RAG version
  python scripts/run_eval.py --model gpt-4o --rag-version rag_v2 --limit 100

  # Evaluate without RAG
  python scripts/run_eval.py --no-rag --limit 30

  # Evaluate specific category
  python scripts/run_eval.py --category booking --limit 20

  # Save results to file
  python scripts/run_eval.py --limit 100 --output results.json
        """,
    )

    parser.add_argument(
        "--model",
        "--model-version",
        type=str,
        default=CHAT_MODEL,
        help=f"Model version to evaluate (default: {CHAT_MODEL})",
    )
    parser.add_argument(
        "--rag-version",
        type=str,
        default=DEFAULT_RAG_VERSION,
        help=f"RAG version identifier (default: {DEFAULT_RAG_VERSION})",
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Disable RAG (use model only)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of examples to evaluate (default: all)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter examples by category (e.g., booking, price, contraindication)",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default=None,
        help="Notes about this evaluation run",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Save results to JSON file",
    )

    args = parser.parse_args()

    # Print header
    logger.info("=" * 70)
    logger.info("LaserOstop CM - Evaluation Runner")
    logger.info("=" * 70)
    logger.info(f"Model: {args.model}")
    logger.info(f"RAG Version: {args.rag_version if not args.no_rag else 'Disabled'}")
    logger.info(f"Use RAG: {not args.no_rag}")
    logger.info(f"Limit: {args.limit or 'All examples'}")
    logger.info(f"Category Filter: {args.category or 'None'}")
    logger.info("=" * 70)

    # Check if database has examples
    from app.db import get_session, EvalExample
    with get_session() as session:
        total_examples = session.query(EvalExample).count()

    if total_examples == 0:
        logger.error("\nNo evaluation examples found in database!")
        logger.info("\nPlease run the seed script first:")
        logger.info("  python scripts/dev_seed.py")
        sys.exit(1)

    logger.info(f"\nTotal examples in database: {total_examples}")

    # Confirm with user if not limiting
    if args.limit is None or args.limit > 50:
        confirm = input(f"\nThis will evaluate {args.limit or 'ALL'} examples. Continue? [y/N] ")
        if confirm.lower() not in ['y', 'yes']:
            logger.info("Evaluation cancelled.")
            sys.exit(0)

    # Run evaluation
    logger.info("\nStarting evaluation...")
    logger.info("This may take several minutes depending on the number of examples.\n")

    try:
        summary = run_evaluation(
            model_version=args.model,
            rag_version=args.rag_version,
            use_rag=not args.no_rag,
            limit=args.limit,
            category_filter=args.category,
            notes=args.notes,
        )

        # Print summary
        print_summary(summary)

        # Save to file if requested
        if args.output:
            save_results_to_file(summary, args.output)

        # Print next steps
        print("\nNext steps:")
        print(f"  1. Review results in database (eval_run_id: {summary.get('eval_run_id')})")
        print("  2. Analyze error patterns in EvalResult table")
        print("  3. Compare with previous runs")
        print("  4. Iterate on prompts, RAG, or model selection")

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
