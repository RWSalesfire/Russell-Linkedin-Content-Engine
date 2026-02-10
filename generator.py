import logging
from datetime import datetime

import anthropic

from calendar_tracker import (
    is_source_on_cooldown,
    would_break_category_rule,
    would_break_persona_rule,
)
from config import (
    ANTHROPIC_API_KEY,
    DAY_TOPIC_WEIGHTS,
    DRAFT_COUNT,
    PERSONAS,
    SONNET_MODEL,
    VOICE_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

DRAFT_SYSTEM_PROMPT = VOICE_SYSTEM_PROMPT + """

You are writing as the persona: {persona}.

Persona voice guidelines:
- The eCommerce Observer: Data-driven, curious, references specific metrics and trends.
  Tone: "I've been watching this closely and here's what the numbers say..."
- The Honest AI User: Pragmatic about AI, shares real experiences (wins AND failures).
  Tone: "I tried this and here's what actually happened..."
- The Sales Realist: Direct, challenges sales dogma, speaks from experience.
  Tone: "Here's what nobody in sales wants to admit..."
- The Human: Reflective, connects business lessons to life, shows vulnerability.
  Tone: "Something happened this week that made me rethink..."

Write a LinkedIn post based on the article provided. Requirements:
1. LENGTH: 100-150 words. This is strict. Count carefully.
2. HOOK: First line must stop the scroll. Make it bold, specific, or surprising.
3. STRUCTURE: Short paragraphs (1-3 sentences). Use line breaks for readability.
4. CTA: End with a question or invitation to comment.
5. NO HASHTAGS in the post body.
6. NO EMOJIS.
7. Write in first person.

After the post, provide:
- ALT_HOOK_1: An alternative opening line
- ALT_HOOK_2: A second alternative opening line
- IMAGE_PROMPT: A DALL-E prompt for an accompanying image (professional, LinkedIn-appropriate)
- PERSONA: {persona}

Format your response exactly like this:
---POST---
[the post text]
---ALT_HOOK_1---
[alternative hook 1]
---ALT_HOOK_2---
[alternative hook 2]
---IMAGE_PROMPT---
[image generation prompt]
---END---"""


def select_stories(articles, history, count=DRAFT_COUNT):
    """Pick top articles applying day-of-week weights, history filters, and category diversity."""
    today = datetime.now().weekday()
    weights = DAY_TOPIC_WEIGHTS.get(today, {})

    # Apply day-of-week weight multipliers to scores
    scored = []
    for article in articles:
        base_score = article.get("total_score", 0)
        category = article.get("category", "")
        multiplier = weights.get(category, 1.0)
        scored.append((article, base_score * multiplier))

    scored.sort(key=lambda x: x[1], reverse=True)

    selected = []
    used_categories = set()

    for article, weighted_score in scored:
        if len(selected) >= count:
            break

        category = article.get("category", "")
        source = article.get("source", "")

        # Skip if same category already selected (enforce diversity)
        if category in used_categories and len(selected) < count - 1:
            continue

        # Skip if category would break streak rule
        if would_break_category_rule(history, category):
            continue

        # Skip if source is on cooldown
        if is_source_on_cooldown(history, source):
            continue

        selected.append(article)
        used_categories.add(category)

    # If we don't have enough, relax diversity constraint
    if len(selected) < count:
        for article, weighted_score in scored:
            if len(selected) >= count:
                break
            if article not in selected:
                selected.append(article)

    return selected[:count]


def assign_personas(articles, history):
    """Match a persona to each article based on category affinity and streak rules."""
    assignments = []
    used_personas = []

    for article in articles:
        category = article.get("category", "")
        best_persona = None
        best_score = -1

        for persona_name, persona_info in PERSONAS.items():
            # Skip if it would break the 3x rule
            if would_break_persona_rule(history, persona_name):
                continue

            # Skip if already used in this batch
            if persona_name in used_personas:
                continue

            # Score by category affinity
            score = 0
            if category in persona_info["preferred_categories"]:
                score = 2
                # Bonus for being first in preference list
                if persona_info["preferred_categories"][0] == category:
                    score = 3

            if score > best_score:
                best_score = score
                best_persona = persona_name

        # Fallback: just pick first unused
        if not best_persona:
            for persona_name in PERSONAS:
                if persona_name not in used_personas:
                    best_persona = persona_name
                    break

        if not best_persona:
            best_persona = list(PERSONAS.keys())[0]

        assignments.append(best_persona)
        used_personas.append(best_persona)

    return assignments


def parse_draft(raw_text):
    """Parse delimiter-based draft output into structured dict."""
    draft = {
        "post": "",
        "alt_hook_1": "",
        "alt_hook_2": "",
        "image_prompt": "",
    }

    sections = {
        "---POST---": "post",
        "---ALT_HOOK_1---": "alt_hook_1",
        "---ALT_HOOK_2---": "alt_hook_2",
        "---IMAGE_PROMPT---": "image_prompt",
    }

    current_key = None
    current_lines = []

    for line in raw_text.split("\n"):
        stripped = line.strip()
        if stripped in sections:
            if current_key:
                draft[current_key] = "\n".join(current_lines).strip()
            current_key = sections[stripped]
            current_lines = []
        elif stripped == "---END---":
            if current_key:
                draft[current_key] = "\n".join(current_lines).strip()
            break
        elif current_key is not None:
            current_lines.append(line)

    # Handle case where ---END--- is missing
    if current_key and not draft[current_key]:
        draft[current_key] = "\n".join(current_lines).strip()

    return draft


def generate_single_draft(article, persona):
    """Generate one draft using Sonnet."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system = DRAFT_SYSTEM_PROMPT.format(persona=persona)

    snippet = (article.get("content") or article.get("summary") or "")[:1500]
    user_text = (
        f"Write a LinkedIn post based on this article.\n\n"
        f"Title: {article['title']}\n"
        f"Source: {article['source']}\n"
        f"Category: {article.get('category', 'General')}\n"
        f"Summary: {article.get('one_line_summary', '')}\n"
        f"Content:\n{snippet}\n\n"
        f"URL: {article.get('url', '')}"
    )

    logger.info(f"Generating draft for: {article['title']} (persona: {persona})")

    response = client.messages.create(
        model=SONNET_MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_text}],
    )

    raw = response.content[0].text
    draft = parse_draft(raw)
    draft["persona"] = persona
    draft["article"] = article
    return draft


def generate_drafts(articles, personas):
    """Generate drafts for all selected articles."""
    drafts = []
    for article, persona in zip(articles, personas):
        try:
            draft = generate_single_draft(article, persona)
            drafts.append(draft)
        except Exception as e:
            logger.error(f"Failed to generate draft for '{article['title']}': {e}")
            continue
    return drafts
