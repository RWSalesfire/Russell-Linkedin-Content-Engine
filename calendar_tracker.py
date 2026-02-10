import json
import logging
from collections import Counter
from datetime import datetime, timedelta

from config import (
    CATEGORIES,
    HISTORY_LOOKBACK_DAYS,
    MAX_SAME_CATEGORY_STREAK,
    MAX_SAME_PERSONA_STREAK,
    SOURCE_COOLDOWN_POSTS,
)

logger = logging.getLogger(__name__)

HISTORY_PATH = "post_history.json"


def load_history(path=HISTORY_PATH):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"posts": []}


def save_history(history, path=HISTORY_PATH):
    with open(path, "w") as f:
        json.dump(history, f, indent=2)


def get_recent_posts(history, days=HISTORY_LOOKBACK_DAYS):
    """Return posts from the last N days."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    return [p for p in history["posts"] if p.get("date", "") >= cutoff]


def get_last_n_posts(history, n):
    """Return the last N posts by date order."""
    sorted_posts = sorted(history["posts"], key=lambda p: p.get("date", ""), reverse=True)
    return sorted_posts[:n]


def would_break_category_rule(history, category):
    """Check if using this category would create a streak > MAX_SAME_CATEGORY_STREAK."""
    recent = get_last_n_posts(history, MAX_SAME_CATEGORY_STREAK)
    return all(p.get("category") == category for p in recent) if recent else False


def would_break_persona_rule(history, persona):
    """Check if using this persona would create a streak > MAX_SAME_PERSONA_STREAK."""
    recent = get_last_n_posts(history, MAX_SAME_PERSONA_STREAK)
    if len(recent) < MAX_SAME_PERSONA_STREAK:
        return False
    return all(p.get("persona") == persona for p in recent)


def is_source_on_cooldown(history, source):
    """Check if a source was used in the last SOURCE_COOLDOWN_POSTS posts."""
    recent = get_last_n_posts(history, SOURCE_COOLDOWN_POSTS)
    return any(p.get("source") == source for p in recent)


def get_category_distribution(history):
    """Get category counts for the last HISTORY_LOOKBACK_DAYS days."""
    recent = get_recent_posts(history)
    counts = Counter(p.get("category", "Unknown") for p in recent)
    return {cat: counts.get(cat, 0) for cat in CATEGORIES}


def record_post(history, date, category, persona, source, angle):
    """Add a post to history."""
    history["posts"].append({
        "date": date,
        "category": category,
        "persona": persona,
        "source": source,
        "angle": angle,
    })
    return history
