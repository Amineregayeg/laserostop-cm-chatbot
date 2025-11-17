#!/usr/bin/env python3
"""
Development seed script for LaserOstop CM Chatbot.

This script seeds the database with sample evaluation examples
for testing and development purposes.

Usage:
    python scripts/dev_seed.py [--clear]

Arguments:
    --clear: Clear existing evaluation examples before seeding
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, EvalExample, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Sample evaluation examples in Tunisian dialect
SAMPLE_EXAMPLES = [
    # Booking / Rendez-vous
    {
        "input_text": "Salam, nheb nhez rendez-vous pour arrêter de fumer",
        "ideal_answer": "Ahla! Barcha farhine bik. Pour réserver rendez-vous, tnajem tséléphéné 3ala [phone] wala tb3athlna message privé. Kifech t7eb?",
        "category": "booking",
        "sensitivity": "normal",
    },
    {
        "input_text": "Kifech nhez rendez-vous?",
        "ideal_answer": "Bassite! Tnajem tséléphéné direct 3ala [phone] wala tb3athlna message 3al Facebook. N7ébou nsem3ouk w net3arfou 3lik akthar.",
        "category": "booking",
        "sensitivity": "normal",
    },
    {
        "input_text": "Je veux prendre rdv, comment faire?",
        "ideal_answer": "Marhba bik! Pour prendre rendez-vous, tnajem tsalli 3al [phone] wala tb3athlna message. Ena nhébou n3awnouk bech taqta3 tabac.",
        "category": "booking",
        "sensitivity": "normal",
    },

    # Price / Pricing
    {
        "input_text": "Chhal thot les séances?",
        "ideal_answer": "Les séances t3andna prix raisonnable. Pour les détails w les tarifs, tnajem tsalli 3al [phone] w nemchiwlek kollech. Chaque cas unique donc prix yetbaddel selon nombre de séances.",
        "category": "price",
        "sensitivity": "normal",
    },
    {
        "input_text": "C'est cher le traitement?",
        "ideal_answer": "Le prix taa3 le traitement mouch ghali rapport au bénéfice taa3 l'arrêt tabac. Tnajem tsalli w n9ouloulek les détails. L'investissement fi sehtek yestahel!",
        "category": "price",
        "sensitivity": "normal",
    },

    # Process / How it works
    {
        "input_text": "Kifech ykhadem le laser?",
        "ideal_answer": "Le laser ykhadem par stimulation de points d'acupuncture sans douleur. Yekhdem 3ala réduire l'envie de fumer w les symptômes taa3 le manque. Barcha nés yestafedhw men première séance!",
        "category": "process",
        "sensitivity": "normal",
    },
    {
        "input_text": "Combien de séances il faut?",
        "ideal_answer": "3adaten 1 à 3 séances selon كل واحد w motivation mte3ou. Barcha nés yaqt3ou men première séance! Ama 9addech ykounu 3andhom besoin de suivi.",
        "category": "process",
        "sensitivity": "normal",
    },
    {
        "input_text": "Est-ce que ça fait mal?",
        "ideal_answer": "Absolument makanech wejja3! Le laser ma3andouch contact avec la peau w ma ت7éséch بشي. C'est relaxant w confortable.",
        "category": "process",
        "sensitivity": "normal",
    },

    # Effectiveness / Success
    {
        "input_text": "Est-ce que ça marche vraiment?",
        "ideal_answer": "Oui! Barcha nés نجحو bech yaqt3ou tabac avec le laser. Le taux de réussite 3ali w'allah ama lazem motivation w volonté mennek! Le laser y3awnek ama enti esor esséyés.",
        "category": "effectiveness",
        "sensitivity": "normal",
    },
    {
        "input_text": "Chkoun jreb w n7all?",
        "ideal_answer": "Barcha clients mte3na n7allou w réussiw bech yaqt3ou tabac définitivement! Chacun 3andou story mte3ou ama l'important hiya motivation w engagement.",
        "category": "effectiveness",
        "sensitivity": "normal",
    },

    # Medical concerns / Contraindications
    {
        "input_text": "أنا حامل، نجم نعمل laser?",
        "ideal_answer": "Pour les femmes enceintes, c'est très important تستشيري طبيبك avant. Ena منجموش نعطيوك conseil médical. Votre médecin هو اللي يقرر si c'est appropriate pour votre situation.",
        "category": "contraindication",
        "sensitivity": "medical_risk",
    },
    {
        "input_text": "J'ai du diabète, je peux faire le laser?",
        "ideal_answer": "Pour les conditions médicales comme le diabète, lazem tstachéri طبيبك first. Ena ma نجموش نعطيو diagnostic wala conseil médical. Votre docteur est le mieux placé pour vous conseiller.",
        "category": "contraindication",
        "sensitivity": "medical_risk",
    },
    {
        "input_text": "Je prends des médicaments, c'est compatible?",
        "ideal_answer": "Si vous prenez des médicaments, il faut absolument en parler maa طبيبك avant. Ena manajmouch نقولوك yes or no car c'est médical decision. Votre médecin ynajem yعطيك le bon conseil.",
        "category": "contraindication",
        "sensitivity": "medical_risk",
    },

    # General info
    {
        "input_text": "Winou l'adresse mte3kom?",
        "ideal_answer": "L'adresse mte3na fi Tunis (détails exacts fi context). Tnajem تجي direct wala tsalli 9bal 3al [phone] bech تتأكد men les horaires.",
        "category": "info",
        "sensitivity": "normal",
    },
    {
        "input_text": "Quels sont vos horaires?",
        "ideal_answer": "Les horaires mte3na (détails fi context). Pour rendez-vous, tsalli 3al [phone] w نحددولك wقت يناسبك.",
        "category": "info",
        "sensitivity": "normal",
    },
]


def seed_eval_examples(clear_existing: bool = False) -> None:
    """
    Seed database with sample evaluation examples.

    Args:
        clear_existing: If True, delete existing eval examples first.
    """
    logger.info("=" * 60)
    logger.info("LaserOstop CM - Development Seed Script")
    logger.info("=" * 60)

    # Initialize database
    init_db()
    logger.info("Database initialized")

    with get_session() as session:
        # Clear existing examples if requested
        if clear_existing:
            count = session.query(EvalExample).count()
            if count > 0:
                logger.info(f"Clearing {count} existing evaluation examples...")
                session.query(EvalExample).delete()
                logger.info("Existing examples cleared")

        # Check current count
        existing_count = session.query(EvalExample).count()
        logger.info(f"Current evaluation examples: {existing_count}")

        # Add sample examples
        logger.info(f"\nAdding {len(SAMPLE_EXAMPLES)} sample examples...")

        for i, example_data in enumerate(SAMPLE_EXAMPLES, 1):
            example = EvalExample(
                input_text=example_data["input_text"],
                ideal_answer=example_data.get("ideal_answer"),
                category=example_data.get("category"),
                sensitivity=example_data.get("sensitivity", "normal"),
            )
            session.add(example)
            logger.info(f"  {i}. [{example_data['category']}] {example_data['input_text'][:50]}...")

        session.commit()

    # Final count
    with get_session() as session:
        final_count = session.query(EvalExample).count()

    logger.info("\n" + "=" * 60)
    logger.info(f"Seeding completed successfully!")
    logger.info(f"Total evaluation examples: {final_count}")
    logger.info("=" * 60)

    # Print category breakdown
    with get_session() as session:
        categories = session.query(
            EvalExample.category,
            session.query(EvalExample).filter(
                EvalExample.category == EvalExample.category
            ).count()
        ).group_by(EvalExample.category).all()

    logger.info("\nCategory breakdown:")
    with get_session() as session:
        from sqlalchemy import func
        category_counts = (
            session.query(
                EvalExample.category,
                func.count(EvalExample.id)
            )
            .group_by(EvalExample.category)
            .all()
        )

        for category, count in category_counts:
            logger.info(f"  {category}: {count}")

    logger.info("\nNext steps:")
    logger.info("  1. Run evaluation: python scripts/run_eval.py --limit 10")
    logger.info("  2. Test chat: python -m app.chat")
    logger.info("  3. Start Flask: python -m app")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Seed database with sample evaluation examples"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing evaluation examples before seeding",
    )

    args = parser.parse_args()

    try:
        seed_eval_examples(clear_existing=args.clear)
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
