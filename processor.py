import logging
import re
from difflib import SequenceMatcher

from bs4 import BeautifulSoup

from config import DEDUP_THRESHOLD

logger = logging.getLogger(__name__)


def strip_html(text):
    """Remove HTML tags and clean up whitespace."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def title_similarity(a, b):
    """Compare two titles using SequenceMatcher."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def content_snippet(article, length=200):
    """Get a clean text snippet from an article for comparison."""
    text = strip_html(article.get("content", "") or article.get("summary", ""))
    return text[:length].lower()


def deduplicate(articles):
    """Remove duplicate articles based on title similarity and content overlap."""
    if not articles:
        return articles

    unique = []
    for article in articles:
        is_dup = False
        for kept in unique:
            sim = title_similarity(article["title"], kept["title"])
            if sim >= DEDUP_THRESHOLD:
                is_dup = True
                break
            # Borderline title match — check content snippets
            if sim >= DEDUP_THRESHOLD - 0.15:
                snippet_a = content_snippet(article)
                snippet_b = content_snippet(kept)
                if snippet_a and snippet_b:
                    content_sim = SequenceMatcher(None, snippet_a, snippet_b).ratio()
                    if content_sim >= 0.6:
                        is_dup = True
                        break
        if not is_dup:
            unique.append(article)

    removed = len(articles) - len(unique)
    if removed:
        logger.info(f"Deduplication removed {removed} articles")
    return unique


def process_articles(articles):
    """Clean HTML and deduplicate articles."""
    for article in articles:
        article["title"] = strip_html(article["title"])
        article["summary"] = strip_html(article["summary"])
        article["content"] = strip_html(article["content"])

    return deduplicate(articles)
