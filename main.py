#!/usr/bin/env python3
"""LinkedIn Content Engine - Daily pipeline orchestrator."""
import argparse
import logging
import sys
from datetime import datetime

from calendar_tracker import (
    get_category_distribution,
    load_history,
    record_post,
    save_history,
)
from categoriser import categorise_and_score
from email_sender import send_daily_digest
from gmail_feeds import fetch_all_newsletters
from generator import assign_personas, generate_drafts, select_stories
from output import output_drafts
from processor import process_articles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline(dry_run=False, feeds_only=False, email_only=False, no_email=False):
    """Execute the full content pipeline."""
    logger.info("Starting LinkedIn Content Engine pipeline")

    # Step 1: Fetch newsletter emails
    logger.info("Step 1/6: Fetching newsletter emails")
    articles = fetch_all_newsletters()
    if not articles:
        logger.warning("No articles fetched. Check Gmail API access and 'Newsletters' label.")
        sys.exit(1)
    logger.info(f"Fetched {len(articles)} articles")

    # Step 2: Process (clean + dedup)
    logger.info("Step 2/6: Processing articles")
    articles = process_articles(articles)
    logger.info(f"{len(articles)} articles after processing")

    if feeds_only:
        print(f"\n--- Newsletters Only Mode ---")
        print(f"Total articles: {len(articles)}\n")
        for i, a in enumerate(articles[:20], 1):
            print(f"{i}. [{a['source']}] {a['title']}")
        return

    # Step 3: Categorise and score
    logger.info("Step 3/6: Categorising and scoring with Haiku")
    articles = categorise_and_score(articles)

    # Step 4: Select stories and assign personas
    logger.info("Step 4/6: Selecting stories and assigning personas")
    history = load_history()
    selected = select_stories(articles, history)
    personas = assign_personas(selected, history)

    logger.info("Selected stories:")
    for article, persona in zip(selected, personas):
        logger.info(
            f"  - {article['title']} [{article.get('category')}] "
            f"(score: {article.get('total_score')}) -> {persona}"
        )

    # Step 5: Generate drafts
    logger.info("Step 5/6: Generating drafts with Sonnet")
    drafts = generate_drafts(selected, personas)
    if not drafts:
        logger.error("No drafts generated")
        sys.exit(1)

    # Step 6: Output to Google Docs
    logger.info("Step 6/7: Outputting drafts to Google Docs")
    category_dist = get_category_distribution(history)

    # Skip Google Docs output if email-only mode
    if not email_only:
        output_drafts(drafts, category_dist, dry_run=dry_run)

    # Step 7: Send email digest
    if not no_email:
        logger.info("Step 7/7: Sending email digest")
        email_success = send_daily_digest(drafts, category_dist, dry_run=dry_run)
        if email_success:
            logger.info("Email digest sent successfully")
        else:
            logger.warning("Email digest failed (pipeline continues)")
    else:
        logger.info("Step 7/7: Skipping email (--no-email flag)")

    # If email-only mode, skip history updates and return early
    if email_only:
        logger.info("Email-only mode complete")
        return

    # Update history (skip in dry-run)
    if not dry_run:
        today = datetime.now().isoformat()[:10]
        for draft in drafts:
            article = draft["article"]
            record_post(
                history,
                date=today,
                category=article.get("category", ""),
                persona=draft["persona"],
                source=article.get("source", ""),
                angle=article.get("one_line_summary", ""),
            )
        save_history(history)
        logger.info("Post history updated")

    logger.info("Pipeline complete")


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Content Engine")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print drafts to console only, don't push to Google Docs or send email, don't update history",
    )
    parser.add_argument(
        "--feeds-only",
        action="store_true",
        help="Only fetch and display newsletter emails, skip generation",
    )
    parser.add_argument(
        "--email-only",
        action="store_true",
        help="Only send email digest (skip Google Docs output and history updates)",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Skip email sending (only output to Google Docs)",
    )
    args = parser.parse_args()

    # Validate conflicting arguments
    if args.email_only and args.no_email:
        parser.error("--email-only and --no-email cannot be used together")

    run_pipeline(
        dry_run=args.dry_run,
        feeds_only=args.feeds_only,
        email_only=args.email_only,
        no_email=args.no_email
    )


if __name__ == "__main__":
    main()
