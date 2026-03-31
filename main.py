#!/usr/bin/env python3
"""LinkedIn Content Engine - Daily pipeline orchestrator."""
import argparse
import json
import logging
import sys
from datetime import datetime

from calendar_tracker import (
    get_category_distribution,
    get_format_distribution,
    load_history,
    record_post,
    save_history,
)
from categoriser import categorise_and_score
from gmail_feeds import fetch_all_newsletters
from generator import assign_personas, generate_drafts, select_stories
from hook_scorer import rank_drafts
from output import output_drafts
from processor import process_articles
from config import REALTIME_ENABLED

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline(dry_run=False, feeds_only=False, forced_format=None, no_realtime=False):
    """Execute the full content pipeline."""
    logger.info("Starting LinkedIn Content Engine pipeline")

    # Step 1: Fetch newsletter emails
    logger.info("Step 1/8: Fetching newsletter emails")
    articles = fetch_all_newsletters()
    if not articles:
        logger.warning("No articles fetched. Check Gmail API access and 'Newsletters' label.")
        sys.exit(1)
    logger.info(f"Fetched {len(articles)} articles")

    # Step 1b: Fetch Hacker News real-time stories
    if REALTIME_ENABLED and not no_realtime:
        logger.info("Step 1b: Fetching Hacker News real-time stories")
        try:
            from realtime_feeds import fetch_hacker_news
            hn_articles = fetch_hacker_news()
            if hn_articles:
                articles.extend(hn_articles)
                logger.info(f"Added {len(hn_articles)} HN articles ({len(articles)} total)")
            else:
                logger.info("No HN articles passed filters")
        except Exception as e:
            logger.warning(f"Hacker News fetch failed (non-fatal): {e}")
    elif no_realtime:
        logger.info("Step 1b: Skipping Hacker News (--no-realtime)")

    # Step 2: Process (clean + dedup)
    logger.info("Step 2/8: Processing articles")
    articles = process_articles(articles)
    logger.info(f"{len(articles)} articles after processing")

    if feeds_only:
        print(f"\n--- Feeds Mode ---")
        print(f"Total articles: {len(articles)}\n")
        for i, a in enumerate(articles[:30], 1):
            source_tag = a.get("source", "Unknown")
            rt = " [RT]" if a.get("source_type") == "realtime" else ""
            print(f"{i}. [{source_tag}{rt}] {a['title']}")
        return

    # Step 3: Categorise and score (7 criteria)
    logger.info("Step 3/8: Categorising and scoring with Haiku (7 criteria)")
    articles = categorise_and_score(articles)

    # Step 4: Select stories + assign formats and personas
    logger.info("Step 4/8: Selecting stories, assigning formats and personas")
    history = load_history()
    selected = select_stories(articles, history, forced_format=forced_format)
    personas = assign_personas(selected, history)

    logger.info("Selected stories:")
    for article, persona in zip(selected, personas):
        fmt = article.get("content_format", "text")
        logger.info(
            f"  - [{fmt.upper()}] {article['title']} [{article.get('category')}] "
            f"(score: {article.get('total_score')}/70) -> {persona}"
        )

    # Step 5: Generate format-specific drafts (4 article-based + 1 original prompt)
    logger.info("Step 5/8: Generating drafts with Sonnet (4 article + 1 original)")
    drafts = generate_drafts(selected, personas)
    if not drafts:
        logger.error("No drafts generated")
        sys.exit(1)
    logger.info(f"Generated {len(drafts)} drafts ({sum(1 for d in drafts if d.get('content_format') != 'original')} article-based, {sum(1 for d in drafts if d.get('content_format') == 'original')} original)")

    # Step 6: Score hooks and rank
    logger.info("Step 6/8: Scoring hooks and ranking drafts")
    drafts = rank_drafts(drafts)
    for draft in drafts:
        logger.info(
            f"  - Hook score: {draft.get('hook_score', 0)} | "
            f"Composite: {draft.get('composite_score', 0)} | "
            f"{draft.get('content_format', 'text').upper()}"
        )

    # Step 7: Output to Google Docs (with engagement plan)
    logger.info("Step 7/8: Outputting drafts to Google Docs")
    category_dist = get_category_distribution(history)
    format_dist = get_format_distribution(history)
    output_drafts(drafts, category_dist, format_dist, dry_run=dry_run)

    # Step 8: Update history (with format) - only record article-based drafts
    # Original prompts aren't recorded until Russell actually writes and posts them
    logger.info("Step 8/8: Updating history")
    if not dry_run:
        today = datetime.now().isoformat()[:10]
        for draft in drafts:
            if draft.get("content_format") == "original":
                continue  # don't record unwritten prompts
            article = draft["article"]
            record_post(
                history,
                date=today,
                category=article.get("category", ""),
                persona=draft.get("persona", ""),
                source=article.get("source", ""),
                angle=article.get("one_line_summary", ""),
                content_format=draft.get("content_format", "text"),
            )
        save_history(history)
        logger.info("Post history updated")

    logger.info("Pipeline complete")


def log_metrics():
    """Prompt for yesterday's post metrics and update history."""
    history = load_history()
    if not history["posts"]:
        print("No posts in history yet.")
        return

    # Find most recent post
    sorted_posts = sorted(history["posts"], key=lambda p: p.get("date", ""), reverse=True)
    recent = sorted_posts[0]

    print(f"\nLogging metrics for: {recent.get('angle', 'Unknown post')}")
    print(f"Date: {recent.get('date', 'Unknown')} | Format: {recent.get('content_format', 'text')}")
    print()

    try:
        impressions = input("Impressions: ").strip()
        comments = input("Comments: ").strip()
        likes = input("Likes (reactions): ").strip()
        reposts = input("Reposts: ").strip()

        recent["metrics"] = {
            "impressions": int(impressions) if impressions else 0,
            "comments": int(comments) if comments else 0,
            "likes": int(likes) if likes else 0,
            "reposts": int(reposts) if reposts else 0,
            "logged_at": datetime.now().isoformat(),
        }

        save_history(history)
        print("\nMetrics saved.")
    except (ValueError, KeyboardInterrupt):
        print("\nMetrics logging cancelled.")


def weekly_summary():
    """Output performance review: posts by format, best hooks, growth metrics."""
    history = load_history()
    if not history["posts"]:
        print("No posts in history yet.")
        return

    from collections import Counter

    # Last 7 days
    from calendar_tracker import get_recent_posts
    recent = get_recent_posts(history, days=7)

    print("\n" + "=" * 50)
    print("  WEEKLY SUMMARY")
    print("=" * 50)

    # Posts this week
    print(f"\nPosts this week: {len(recent)}")

    # Format distribution
    format_counts = Counter(p.get("content_format", "text") for p in recent)
    print("\nFormat Distribution:")
    for fmt, count in format_counts.most_common():
        print(f"  - {fmt}: {count}")

    # Category distribution
    cat_counts = Counter(p.get("category", "Unknown") for p in recent)
    print("\nCategory Distribution:")
    for cat, count in cat_counts.most_common():
        print(f"  - {cat}: {count}")

    # Persona distribution
    persona_counts = Counter(p.get("persona", "Unknown") for p in recent)
    print("\nPersona Distribution:")
    for persona, count in persona_counts.most_common():
        print(f"  - {persona}: {count}")

    # Metrics summary (if any posts have metrics)
    posts_with_metrics = [p for p in recent if "metrics" in p]
    if posts_with_metrics:
        print("\nPerformance (posts with metrics logged):")
        total_impressions = sum(p["metrics"].get("impressions", 0) for p in posts_with_metrics)
        total_comments = sum(p["metrics"].get("comments", 0) for p in posts_with_metrics)
        total_likes = sum(p["metrics"].get("likes", 0) for p in posts_with_metrics)

        print(f"  Total impressions: {total_impressions:,}")
        print(f"  Total comments: {total_comments}")
        print(f"  Total likes: {total_likes}")
        print(f"  Avg impressions/post: {total_impressions // len(posts_with_metrics):,}")

        # Best performing by impressions
        best = max(posts_with_metrics, key=lambda p: p["metrics"].get("impressions", 0))
        print(f"\n  Best performer: {best.get('angle', 'Unknown')}")
        print(f"    Format: {best.get('content_format', 'text')} | Impressions: {best['metrics'].get('impressions', 0):,}")

        # Format performance
        format_impressions = {}
        for p in posts_with_metrics:
            fmt = p.get("content_format", "text")
            if fmt not in format_impressions:
                format_impressions[fmt] = []
            format_impressions[fmt].append(p["metrics"].get("impressions", 0))

        if format_impressions:
            print("\n  Avg impressions by format:")
            for fmt, imps in sorted(format_impressions.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True):
                avg = sum(imps) // len(imps)
                print(f"    - {fmt}: {avg:,} ({len(imps)} posts)")

    # Growth estimate
    total_posts = len(history["posts"])
    print(f"\nTotal posts in history: {total_posts}")
    print(f"Current followers: 7,316 (update manually)")
    print(f"Target: 10,000")
    print(f"Gap: 2,684 followers")

    # Estimate based on current rate
    if posts_with_metrics:
        avg_imp = total_impressions // len(posts_with_metrics)
        # Rough estimate: ~1 follower per 50 impressions
        est_followers_per_week = (avg_imp * len(recent)) // 50
        if est_followers_per_week > 0:
            weeks_to_target = 2684 // est_followers_per_week
            print(f"Estimated new followers/week (from impressions): ~{est_followers_per_week}")
            print(f"Estimated weeks to 10K: ~{weeks_to_target}")

    print("\n" + "=" * 50)


def main():
    parser = argparse.ArgumentParser(description="LinkedIn Content Engine")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print drafts to console only, don't push to Google Docs, don't update history",
    )
    parser.add_argument(
        "--feeds-only",
        action="store_true",
        help="Only fetch and display newsletter emails, skip generation",
    )
    parser.add_argument(
        "--format",
        choices=["text", "carousel", "poll", "opinion", "story_prompt"],
        help="Force a specific content format for all drafts (for testing)",
    )
    parser.add_argument(
        "--log-metrics",
        action="store_true",
        help="Log yesterday's post metrics (impressions, comments, likes)",
    )
    parser.add_argument(
        "--weekly-summary",
        action="store_true",
        help="Output weekly performance summary",
    )
    parser.add_argument(
        "--sync-obsidian",
        action="store_true",
        help="Backfill all post history into Obsidian vault post logs",
    )
    parser.add_argument(
        "--no-realtime",
        action="store_true",
        help="Skip Hacker News real-time feed (newsletters only)",
    )
    args = parser.parse_args()

    if args.sync_obsidian:
        history = load_history()
        try:
            from obsidian_output import sync_all
            sync_all(history)
            logger.info("Obsidian vault sync complete")
        except Exception as e:
            logger.error(f"Obsidian sync failed: {e}")
        return

    if args.log_metrics:
        log_metrics()
        # Update Obsidian dashboard after logging metrics
        try:
            from obsidian_output import update_dashboard
            history = load_history()
            update_dashboard(history)
        except Exception as e:
            logger.warning(f"Obsidian dashboard update failed (non-fatal): {e}")
        return

    if args.weekly_summary:
        weekly_summary()
        # Update Obsidian dashboard after weekly summary
        try:
            from obsidian_output import update_dashboard
            history = load_history()
            update_dashboard(history)
        except Exception as e:
            logger.warning(f"Obsidian dashboard update failed (non-fatal): {e}")
        return

    run_pipeline(
        dry_run=args.dry_run,
        feeds_only=args.feeds_only,
        forced_format=args.format,
        no_realtime=args.no_realtime,
    )


if __name__ == "__main__":
    main()
