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
    CONTENT_PILLARS,
    DAY_FORMAT_MAP,
    DAY_TOPIC_WEIGHTS,
    DRAFT_COUNT,
    PERSONAS,
    SONNET_MODEL,
    VOICE_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

# Russell's outsider context - added to all prompts
OUTSIDER_CONTEXT = """Russell came from 5+ years in traditional media (radio, OOH) before moving to digital eCommerce. He sees what digital natives miss: single-minded propositions, brand building over clicks, reach/frequency fundamentals, creative quality over channel optimisation."""

DRAFT_SYSTEM_PROMPT = VOICE_SYSTEM_PROMPT + """

""" + OUTSIDER_CONTEXT + """

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

Content pillar context: {pillar_context}

Write a LinkedIn post based on the article provided. Requirements:
1. LENGTH: 200-300 words. This is strict. Count carefully.
2. HOOK: First line must be under 12 words and contain a specific detail - a number, name, or timeframe. The first 210 characters must make a complete claim, not a teaser.
3. STRUCTURE: Short paragraphs (1-3 sentences). Use line breaks for readability.
4. ENDINGS: Vary endings. Not every post needs a question. Some posts end with a statement that sits with the reader.
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

CAROUSEL_PROMPT = VOICE_SYSTEM_PROMPT + """

""" + OUTSIDER_CONTEXT + """

Content pillar context: {pillar_context}

Generate a LinkedIn carousel post (5-6 slides) based on the article provided. This will be pasted into aiCarousels.com.

Requirements:
1. SLIDE 1: Provocative title, max 8 words. Must stop the scroll.
2. SLIDES 2-5: One clear point per slide. Include a specific data point, stat, or named example on each slide. Keep text to 2-3 short sentences per slide.
3. SLIDE 6: CTA slide - "Follow for more [topic]" or a specific question to drive comments.
4. Use Russell's challenger tone throughout.
5. No jargon, no fluff, no emojis.
6. British English.

Format your response exactly like this:
---SLIDE_1---
[title slide text]
---SLIDE_2---
[point 1]
---SLIDE_3---
[point 2]
---SLIDE_4---
[point 3]
---SLIDE_5---
[point 4]
---SLIDE_6---
[CTA slide]
---CAPTION---
[2-3 sentence LinkedIn caption to accompany the carousel. Include a question or bold claim.]
---END---"""

POLL_PROMPT = VOICE_SYSTEM_PROMPT + """

""" + OUTSIDER_CONTEXT + """

Content pillar context: {pillar_context}

Generate a LinkedIn poll based on the article provided.

Requirements:
1. CONTEXT: 2-3 sentences framing the debate. Reference the article's key finding or claim. Make it provocative enough to demand a vote.
2. QUESTION: A polarising question. NOT yes/no. Force a choice between positions.
3. OPTIONS: Exactly 4 options:
   - Option 1: The expected/mainstream answer
   - Option 2: The contrarian position
   - Option 3: The pragmatic middle ground
   - Option 4: The provocative wildcard
4. Keep each option under 30 characters (LinkedIn poll limit).
5. British English. No emojis.

Format your response exactly like this:
---CONTEXT---
[2-3 sentence context paragraph]
---QUESTION---
[the poll question]
---OPTION_1---
[expected answer]
---OPTION_2---
[contrarian answer]
---OPTION_3---
[pragmatic answer]
---OPTION_4---
[provocative wildcard]
---END---"""

OPINION_PROMPT = VOICE_SYSTEM_PROMPT + """

""" + OUTSIDER_CONTEXT + """

Content pillar context: {pillar_context}

Write a bold opinion/hot take LinkedIn post based on the article provided. This is the "Thursday hot take" format.

Requirements:
1. LENGTH: 250-350 words. This is strict.
2. HOOK: Bold opening claim in the first line. Under 12 words. Make it a statement people will disagree with.
3. BODY: Back up the claim with evidence from the article, then add a section marked [Personal angle placeholder - add your experience here] where Russell should insert his own story or example.
4. ENDING: End with a conversation-starting question that forces people to pick a side.
5. Challenger tone dialled up to maximum. Be direct. Be provocative. Challenge the industry consensus.
6. NO HASHTAGS, NO EMOJIS.
7. British English. First person.

Format your response exactly like this:
---POST---
[the hot take post]
---ALT_HOOK_1---
[alternative opening line]
---ALT_HOOK_2---
[alternative opening line]
---END---"""

STORY_PROMPT_PROMPT = VOICE_SYSTEM_PROMPT + """

""" + OUTSIDER_CONTEXT + """

Content pillar context: {pillar_context}

You are NOT writing a finished post. You are creating a writing scaffold that Russell will complete in 15 minutes.

Based on the article provided, generate a personal story prompt that connects the article's theme to Russell's experience (traditional media background, move to digital, daily AI use, sales reality).

Requirements:
1. TRENDING ANGLE: What's the article's core insight that Russell's audience would care about?
2. SUGGESTED HOOK: Write 2 hook options in confession format ("I spent...", "I was wrong about...") or specific-number format ("After 5 years in radio..."). Under 12 words each.
3. TALKING POINTS: 3 specific points Russell could make, connecting the article to his experience.
4. SUGGESTED STRUCTURE: Brief outline (hook, setup, insight, payoff).
5. WORD TARGET: 300-400 words for the finished piece.

Format your response exactly like this:
---NEEDS_RUSSELL_INPUT---
WRITING PROMPT - This is a scaffold, not a finished post.

TRENDING ANGLE:
[what the article reveals that Russell's audience needs to hear]

SUGGESTED HOOKS:
1. [confession or specific-number hook option 1]
2. [confession or specific-number hook option 2]

TALKING POINTS:
1. [point connecting article to Russell's experience]
2. [point connecting article to Russell's experience]
3. [point connecting article to Russell's experience]

SUGGESTED STRUCTURE:
- Hook: [format suggestion]
- Setup: [1-2 sentences framing the problem]
- Insight: [Russell's personal take, referencing his background]
- Payoff: [ending approach - statement or question]

WORD TARGET: 300-400 words
---END---"""


def get_pillar_context(category):
    """Return the most relevant content pillar description for an article's category."""
    pillar_map = {
        "AI": "The AI Realist",
        "AI in Sales": "Sales Without the Script",
        "AI in eCommerce": "The AI Realist",
        "eCommerce": "Fix the Basics First",
        "Email Marketing": "Fix the Basics First",
        "Behavioural Science": "The Digital Outsider",
        "Sales": "Sales Without the Script",
    }
    pillar_name = pillar_map.get(category, "The Digital Outsider")
    return f"{pillar_name}: {CONTENT_PILLARS[pillar_name]}"


def select_stories(articles, history, count=DRAFT_COUNT, forced_format=None):
    """Pick top articles applying day-of-week weights, history filters, category diversity, and format assignment."""
    today = datetime.now().weekday()
    weights = DAY_TOPIC_WEIGHTS.get(today, {})
    today_format = forced_format or DAY_FORMAT_MAP.get(today, "text")

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

    selected = selected[:count]

    # Assign formats to selected articles
    assign_formats(selected, today_format)

    return selected


def assign_formats(articles, today_format):
    """Assign content format to each article based on day and article scores."""
    if not articles:
        return

    if today_format == "carousel":
        # Carousel goes to highest data_richness article
        best_data = max(articles, key=lambda a: a.get("scores", {}).get("data_richness", 0))
        best_data["content_format"] = "carousel"
        for a in articles:
            if "content_format" not in a:
                a["content_format"] = "text"
    elif today_format == "story_prompt":
        # Story prompt goes to highest confession_potential article
        best_story = max(articles, key=lambda a: a.get("scores", {}).get("confession_potential", 0))
        best_story["content_format"] = "story_prompt"
        for a in articles:
            if "content_format" not in a:
                a["content_format"] = "text"
    elif today_format == "poll":
        # Poll goes to highest contrarian_potential article
        best_poll = max(articles, key=lambda a: a.get("scores", {}).get("contrarian_potential", 0))
        best_poll["content_format"] = "poll"
        for a in articles:
            if "content_format" not in a:
                a["content_format"] = "text"
    elif today_format == "opinion":
        # Opinion goes to highest contrarian_potential article
        best_opinion = max(articles, key=lambda a: a.get("scores", {}).get("contrarian_potential", 0))
        best_opinion["content_format"] = "opinion"
        for a in articles:
            if "content_format" not in a:
                a["content_format"] = "text"
    else:
        for a in articles:
            a["content_format"] = "text"


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
    draft = {}

    # All possible section delimiters across formats
    sections = {
        "---POST---": "post",
        "---ALT_HOOK_1---": "alt_hook_1",
        "---ALT_HOOK_2---": "alt_hook_2",
        "---IMAGE_PROMPT---": "image_prompt",
        "---SLIDE_1---": "slide_1",
        "---SLIDE_2---": "slide_2",
        "---SLIDE_3---": "slide_3",
        "---SLIDE_4---": "slide_4",
        "---SLIDE_5---": "slide_5",
        "---SLIDE_6---": "slide_6",
        "---CAPTION---": "caption",
        "---CONTEXT---": "context",
        "---QUESTION---": "question",
        "---OPTION_1---": "option_1",
        "---OPTION_2---": "option_2",
        "---OPTION_3---": "option_3",
        "---OPTION_4---": "option_4",
        "---NEEDS_RUSSELL_INPUT---": "story_scaffold",
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
    if current_key and current_key not in draft:
        draft[current_key] = "\n".join(current_lines).strip()

    return draft


def get_format_prompt(content_format, persona, pillar_context):
    """Return the appropriate system prompt for the given content format."""
    if content_format == "carousel":
        return CAROUSEL_PROMPT.format(pillar_context=pillar_context)
    elif content_format == "poll":
        return POLL_PROMPT.format(pillar_context=pillar_context)
    elif content_format == "opinion":
        return OPINION_PROMPT.format(pillar_context=pillar_context)
    elif content_format == "story_prompt":
        return STORY_PROMPT_PROMPT.format(pillar_context=pillar_context)
    else:
        return DRAFT_SYSTEM_PROMPT.format(persona=persona, pillar_context=pillar_context)


def generate_single_draft(article, persona, content_format=None):
    """Generate one draft using Sonnet."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    fmt = content_format or article.get("content_format", "text")
    pillar_context = get_pillar_context(article.get("category", ""))
    system = get_format_prompt(fmt, persona, pillar_context)

    snippet = (article.get("content") or article.get("summary") or "")[:1500]
    user_text = (
        f"Write a LinkedIn {fmt} post based on this article.\n\n"
        f"Title: {article['title']}\n"
        f"Source: {article['source']}\n"
        f"Category: {article.get('category', 'General')}\n"
        f"Summary: {article.get('one_line_summary', '')}\n"
        f"Content:\n{snippet}\n\n"
        f"URL: {article.get('url', '')}"
    )

    max_tokens = 1500 if fmt in ("carousel", "story_prompt") else 1024

    logger.info(f"Generating {fmt} draft for: {article['title']} (persona: {persona})")

    response = client.messages.create(
        model=SONNET_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_text}],
    )

    raw = response.content[0].text
    draft = parse_draft(raw)
    draft["persona"] = persona
    draft["article"] = article
    draft["content_format"] = fmt
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
