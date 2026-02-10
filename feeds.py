import json
import logging
from datetime import datetime, timedelta, timezone

import feedparser
import requests

from config import LOOKBACK_HOURS

logger = logging.getLogger(__name__)


def load_feeds_config(path="feeds_config.json"):
    with open(path) as f:
        return json.load(f)["feeds"]


def parse_published_date(entry):
    """Extract a timezone-aware published datetime from a feed entry."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return None


def extract_content(entry):
    """Pull the best available content from a feed entry."""
    if hasattr(entry, "content") and entry.content:
        return entry.content[0].get("value", "")
    if hasattr(entry, "summary"):
        return entry.summary
    return ""


def fetch_feed(feed_config, cutoff):
    """Fetch and filter a single RSS feed. Returns list of article dicts."""
    url = feed_config["url"]
    name = feed_config["name"]
    category_hint = feed_config["category_hint"]
    articles = []

    urls_to_try = [url]
    # Beehiiv fallback: if URL ends with /feed, also try /rss
    if url.endswith("/feed"):
        urls_to_try.append(url.rsplit("/feed", 1)[0] + "/rss")
    elif url.endswith("/rss"):
        urls_to_try.append(url.rsplit("/rss", 1)[0] + "/feed")

    parsed = None
    for try_url in urls_to_try:
        try:
            resp = requests.get(try_url, timeout=15, headers={
                "User-Agent": "LinkedIn-Content-Engine/1.0"
            })
            resp.raise_for_status()
            parsed = feedparser.parse(resp.text)
            if parsed.entries:
                break
        except Exception as e:
            logger.warning(f"Failed to fetch {try_url}: {e}")
            continue

    if not parsed or not parsed.entries:
        logger.warning(f"No entries found for {name} ({url})")
        return articles

    for entry in parsed.entries:
        pub_date = parse_published_date(entry)
        if pub_date and pub_date < cutoff:
            continue

        title = getattr(entry, "title", "Untitled")
        link = getattr(entry, "link", "")
        summary = getattr(entry, "summary", "")
        content = extract_content(entry)

        articles.append({
            "title": title,
            "summary": summary,
            "content": content,
            "url": link,
            "published": pub_date.isoformat() if pub_date else None,
            "source": name,
            "category_hint": category_hint,
        })

    logger.info(f"{name}: {len(articles)} articles in last {LOOKBACK_HOURS}h")
    return articles


def fetch_all_feeds(config_path="feeds_config.json"):
    """Fetch all RSS feeds and return articles from the last LOOKBACK_HOURS."""
    feeds = load_feeds_config(config_path)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    all_articles = []

    for feed_config in feeds:
        try:
            articles = fetch_feed(feed_config, cutoff)
            all_articles.extend(articles)
        except Exception as e:
            logger.error(f"Error processing {feed_config['name']}: {e}")
            continue

    logger.info(f"Total articles fetched: {len(all_articles)}")
    return all_articles
