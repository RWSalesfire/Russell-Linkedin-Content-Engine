"""Hook quality scoring and draft ranking."""
import re

from config import HOOK_PATTERNS

# Words that signal generic AI-generated content
BANNED_WORDS = [
    "delve", "intricate", "tapestry", "pivotal", "underscore", "landscape",
    "foster", "testament", "enhance", "crucial", "comprehensive", "multifaceted",
    "nuanced", "groundbreaking", "cutting-edge", "game-changer", "paradigm",
    "synergy", "realm", "beacon", "cornerstone",
]

GENERIC_OPENERS = [
    "just read", "interesting", "great piece", "great article", "this is why",
    "here's the thing", "let's talk about", "can we talk about",
]


def score_hook(text: str) -> int:
    """Score a hook 0-100 based on specificity, brevity, and pattern match."""
    if not text:
        return 0

    score = 50  # baseline
    text_lower = text.lower()
    words = text.split()

    # Specificity bonuses
    if re.search(r"\d", text):
        score += 15  # contains a number
    if re.search(r"[£$]\d", text):
        score += 10  # money amount
    # Proper noun check (capitalised word that isn't first word)
    if any(w[0].isupper() for w in words[1:] if w):
        score += 5

    # Brevity bonuses
    word_count = len(words)
    if word_count <= 8:
        score += 15
    elif word_count <= 12:
        score += 10
    elif word_count > 20:
        score -= 15

    # Pattern bonuses - confession
    for pattern in HOOK_PATTERNS.get("confession", []):
        if text_lower.startswith(pattern.lower()):
            score += 20
            break

    # Pattern bonuses - bold claim
    for pattern in HOOK_PATTERNS.get("bold_claim", []):
        if pattern.lower() in text_lower:
            score += 15
            break

    # Pattern bonuses - specific number (regex patterns)
    for pattern in HOOK_PATTERNS.get("specific_number", []):
        if re.search(pattern, text):
            score += 10
            break

    # Penalty for generic openers
    for opener in GENERIC_OPENERS:
        if text_lower.startswith(opener):
            score -= 25
            break

    # Penalty for banned words
    for word in BANNED_WORDS:
        if word in text_lower:
            score -= 20

    return min(100, max(0, score))


def get_hook(draft: dict) -> str:
    """Extract the hook (first line) from a draft."""
    post = draft.get("post") or draft.get("context") or draft.get("story_scaffold") or ""
    first_line = post.split("\n")[0].strip() if post else ""
    return first_line


def rank_drafts(drafts: list) -> list:
    """Rank drafts by weighted score: 40% article + 40% hook + 20% format freshness."""
    scored_drafts = []

    for draft in drafts:
        article = draft.get("article", {})
        total_score = article.get("total_score", 0)

        # Normalise article score to 0-100 (max possible is 70)
        article_score_norm = (total_score / 70) * 100 if total_score else 0

        # Score the hook
        hook_text = get_hook(draft)
        hook_score = score_hook(hook_text)

        # Format freshness bonus (non-text formats get a boost)
        content_format = draft.get("content_format", "text")
        format_bonus = 0
        if content_format in ("carousel", "poll"):
            format_bonus = 80
        elif content_format in ("opinion", "story_prompt"):
            format_bonus = 60
        else:
            format_bonus = 40

        # Weighted composite: 40% article + 40% hook + 20% format
        composite = (article_score_norm * 0.4) + (hook_score * 0.4) + (format_bonus * 0.2)

        draft["hook_score"] = hook_score
        draft["composite_score"] = round(composite, 1)
        scored_drafts.append(draft)

    scored_drafts.sort(key=lambda d: d.get("composite_score", 0), reverse=True)
    return scored_drafts
