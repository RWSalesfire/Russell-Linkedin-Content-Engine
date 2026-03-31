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
    ARTICLE_DRAFT_COUNT,
    CONTENT_PILLARS,
    DAY_FORMAT_MAP,
    DAY_TOPIC_WEIGHTS,
    DRAFT_COUNT,
    ORIGINAL_PROMPT_TYPES,
    PERSONAL_ANGLE_BANK,
    PERSONAS,
    PURE_AI_PENALTY,
    REALTIME_BONUS,
    SONNET_MODEL,
    VOICE_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

# Russell's outsider context - only added when persona is Sales Realist or category is Sales
OUTSIDER_CONTEXT = """Russell came from 5+ years in traditional media (radio, OOH) before moving to digital eCommerce. He sees what digital natives miss: single-minded propositions, brand building over clicks, reach/frequency fundamentals, creative quality over channel optimisation."""

# Anti-hallucination rules - prepended to all generation prompts
ANTI_HALLUCINATION_RULES = """
CRITICAL RULES - DO NOT BREAK THESE:
1. NEVER invent personal experiences, events, conferences, conversations, or anecdotes. If the post needs a personal angle and you don't have one, insert a [SCAFFOLD] placeholder asking Russell to add his own.
2. NEVER claim Russell attended, spoke at, visited, or experienced something unless the source article is specifically about him.
3. NEVER fabricate statistics, company names, or results. Only use data from the source article.
4. If you cannot write a compelling post without making something up, write a scaffold prompt instead.
5. Personal angles should ONLY appear when directly relevant to the topic. Do not force personal content.
"""

DRAFT_SYSTEM_PROMPT = VOICE_SYSTEM_PROMPT + """
""" + ANTI_HALLUCINATION_RULES + """
{outsider_context}

You are writing as the persona: {persona}.

Persona voice guidelines:
- The Honest AI User: Pragmatic about AI, shares real experiences (wins AND failures).
  Tone: "I tried this and here's what actually happened..."
- The Sales Realist: Direct, challenges sales dogma, speaks from experience.
  Tone: "Here's what nobody in sales wants to admit..."
- The eCommerce Observer: Data-driven, curious, references specific metrics and trends.
  Tone: "I've been watching this closely and here's what the numbers say..."
- The Human: Reflective, connects business lessons to life, shows vulnerability.
  Tone: "Something happened this week that made me rethink..."

Content pillar context: {pillar_context}

Write a LinkedIn post based on the article provided. Requirements:
1. LENGTH: 200-300 words. This is strict.
2. HOOK: First line must be under 12 words and contain a specific detail - a number, name, or timeframe. Make a complete claim, not a teaser.
3. STRUCTURE: Vary paragraph length. Some lines are one word. Some are a few sentences. Don't make every paragraph the same size. Use white space.
4. ENDINGS: Mix it up. End with a blunt statement. Or a question. Or just stop mid-thought because the point is made. Don't always tie a bow on it.
5. NO HASHTAGS. NO EMOJIS.
6. First person. Write like you're telling a mate about something you read, not presenting at a conference.
7. Pick ONE angle from the article that's interesting. Don't summarise the whole thing. React to the bit that matters.
8. If the post would benefit from a personal experience but you don't have one, add a line: [YOUR TAKE: What's your experience with X? Add 1-2 sentences here.] Do NOT invent a personal story.

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
""" + ANTI_HALLUCINATION_RULES + """
{outsider_context}

Content pillar context: {pillar_context}

Generate a LinkedIn carousel post (8-10 slides) based on the article provided.

Requirements:
1. SLIDE 1 (Hook): Max 8 words. Specific, bold claim or number. This is the only thing people see before swiping. Make it count. No logos, no "A thread on...", no generic titles.
2. SLIDES 2-8: One clear point per slide. Max 40 words per slide. Each slide needs a bold mini-headline (5-7 words) followed by 1-2 short sentences. Include a specific data point, stat, or named example where possible. Each slide should make sense on its own but build on the last.
3. SLIDE 9 (Summary): Recap the 3-4 strongest points in a quick list. This is the slide people screenshot and save.
4. SLIDE 10 (CTA): One clear action. Vary between: a specific question that drives comments, "Save this for your next [specific task]", or "Follow for weekly [specific topic]". Don't use all three. Pick one.

Structure guidance (pick the best fit for this article):
- Step-by-step / How-to: "How to do X without Y" then one step per slide
- Framework: Name it, then one element per slide
- Myth vs Reality: Each slide pairs a common belief with the data
- Problem > Insight > Solution: Validate the problem (2-3 slides), explain why it persists (2 slides), deliver the fix (3 slides)
- Listicle: One tip/mistake/lesson per slide with a specific example

Tone: Same as Russell's text posts. Not polished presentation slides. Write like you're explaining something to a smart colleague, not delivering a keynote.

No jargon, no fluff, no emojis. British English.

Format your response exactly like this:
---SLIDE_1---
[hook slide - max 8 words]
---SLIDE_2---
[point 1: bold headline + 1-2 sentences]
---SLIDE_3---
[point 2]
---SLIDE_4---
[point 3]
---SLIDE_5---
[point 4]
---SLIDE_6---
[point 5]
---SLIDE_7---
[point 6]
---SLIDE_8---
[point 7]
---SLIDE_9---
[summary slide - recap key points]
---SLIDE_10---
[CTA slide - one clear action]
---CAPTION---
[LinkedIn caption. First line must be a complete hook under 140 characters (mobile truncation point). Then a line break. Then 1-2 sentences that complement the carousel without repeating it. No hashtags.]
---END---"""

SCAFFOLD_INTERVIEW_PROMPT = VOICE_SYSTEM_PROMPT + """
""" + ANTI_HALLUCINATION_RULES + """
{outsider_context}

Content pillar context: {pillar_context}

You are NOT writing a finished post. You are creating a decision prompt for Russell to pick an angle and add his real experience.

Based on the article provided, generate 3 specific angles Russell could take. Frame them as strong opinions he could own. Make them specific enough that he can immediately say "yes that's me" or "no, not my take".

Requirements:
1. TRENDING ANGLE: One sentence on what the article reveals that Russell's audience would care about.
2. PICK YOUR ANGLE: 3 options. Each a punchy opinion statement (not a question). One should be the expected take, one contrarian, one tied to personal experience.
3. YOUR INPUT: Tell Russell exactly what to write. Be specific about what kind of experience to share.
4. SUGGESTED HOOKS: 2 hook options, under 12 words each, with a specific detail.

Format your response exactly like this:
---NEEDS_RUSSELL_INPUT---
SCAFFOLD - Pick an angle and add your take.

TRENDING ANGLE:
[what the article reveals that matters]

PICK YOUR ANGLE:
(a) "[strong opinion - the expected take]"
(b) "[strong opinion - the contrarian take]"
(c) "[strong opinion - the personal experience take]"

YOUR INPUT:
Pick one. Write 3-4 sentences about your experience. Be specific - name a tool, a call, a prospect reaction, a number. We'll build the post around it.

SUGGESTED HOOKS:
1. [hook option 1]
2. [hook option 2]
---END---"""

OPINION_PROMPT = VOICE_SYSTEM_PROMPT + """
""" + ANTI_HALLUCINATION_RULES + """
{outsider_context}

Content pillar context: {pillar_context}

Write a bold opinion/hot take LinkedIn post based on the article provided. This is the "Thursday hot take" format.

Requirements:
1. LENGTH: 250-350 words. This is strict.
2. HOOK: Bold opening claim in the first line. Under 12 words. Something people will disagree with. State it like fact.
3. BODY: Don't walk through the article point by point. React to it. What's wrong with the consensus view? Back it up with one or two strong points, not five weak ones. If a personal angle would strengthen the take, add [YOUR TAKE: specific question about Russell's experience]. Do NOT invent a personal story.
4. ENDING: Can be a question. Can also just be a blunt statement that sits with the reader. Don't always ask.
5. Challenger tone up. Be direct. But don't be performatively contrarian. Mean it.
6. NO HASHTAGS, NO EMOJIS.
7. British English. First person. Write like you're slightly annoyed about something, not presenting a thesis.

Format your response exactly like this:
---POST---
[the hot take post]
---ALT_HOOK_1---
[alternative opening line]
---ALT_HOOK_2---
[alternative opening line]
---END---"""

ORIGINAL_PROMPT_SYSTEM = VOICE_SYSTEM_PROMPT + """
""" + ANTI_HALLUCINATION_RULES + """

You are generating a writing prompt for Russell based on his daily work. This is for ORIGINAL content - no article needed. This is the content that builds a personal brand.

Russell's daily reality:
- BDM at Salesfire (eCommerce optimisation SaaS)
- Conducts discovery calls daily, runs product demos and sales presentations
- Manages proof of concepts and ties results to retailer problems
- Building side projects: Sales Call Coaching Dashboard, maternity pay calculator, demo analyser, WooCommerce plugins
- Has kids, juggles work and family
- Came from traditional media (radio, OOH) before digital - but only reference when relevant
- Goes against the grain on outbound and sales methodology

Generate a writing prompt for TODAY's original post. Pick the prompt type provided and frame it as 2-3 specific questions Russell can answer in 3-4 sentences.

Requirements:
1. Questions must be specific enough to trigger a real memory or opinion, not vague.
2. Suggest 2 hook options for the finished post.
3. Keep it tight - Russell has 15 minutes for this.
4. The finished post should be 200-300 words.

Format your response exactly like this:
---NEEDS_RUSSELL_INPUT---
ORIGINAL POST - No article needed. This one's all you.

PROMPT TYPE: [type name]

YOUR QUESTIONS:
[2-3 specific questions for Russell to answer - be pointed, trigger a real memory]

SUGGESTED HOOKS:
1. [hook option 1 - under 12 words, specific detail]
2. [hook option 2 - under 12 words, specific detail]

TIME: 15 minutes. Answer the questions above in 3-4 sentences. Be specific. We'll shape it into a post.
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


def select_stories(articles, history, count=ARTICLE_DRAFT_COUNT, forced_format=None):
    """Pick top articles applying day-of-week weights, history filters, category diversity, and format assignment.

    Selects ARTICLE_DRAFT_COUNT (4) articles. The 5th draft is an original prompt (no article).
    Pure 'AI' category articles are deprioritised - we want 'AI in Sales' and 'AI in eCommerce' instead.
    """
    today = datetime.now().weekday()
    weights = DAY_TOPIC_WEIGHTS.get(today, {})
    today_format = forced_format or DAY_FORMAT_MAP.get(today, "text")

    # Apply day-of-week weight multipliers, realtime bonus, and AI penalty to scores
    scored = []
    for article in articles:
        base_score = article.get("total_score", 0)
        if article.get("source_type") == "realtime":
            base_score += REALTIME_BONUS
        category = article.get("category", "")
        multiplier = weights.get(category, 1.0)
        # Deprioritise generic AI news - we want AI in Sales/eCommerce, not AI industry news
        if category == "AI":
            multiplier *= PURE_AI_PENALTY
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
    """Assign content format to each article based on day and article scores.

    Mix for 4 article-based drafts:
    - 1x day-specific format (carousel on Tue/Fri, opinion on Thu, text otherwise)
    - 1x scaffold interview (always - highest personal_angle_potential article)
    - 2x text (remaining articles)

    The 5th draft (original prompt, no article) is handled separately.
    """
    if not articles:
        return

    assigned = set()

    # 1. Assign day-specific format to best-suited article
    if today_format == "carousel":
        best = max(articles, key=lambda a: a.get("scores", {}).get("carousel_suitability", 0))
        best["content_format"] = "carousel"
        assigned.add(id(best))
    elif today_format == "opinion":
        best = max(articles, key=lambda a: a.get("scores", {}).get("contrarian_potential", 0))
        best["content_format"] = "opinion"
        assigned.add(id(best))

    # 2. Assign scaffold to the best remaining article for personal angle
    remaining = [a for a in articles if id(a) not in assigned]
    if remaining:
        best_scaffold = max(remaining, key=lambda a: a.get("scores", {}).get("personal_angle_potential", 0))
        best_scaffold["content_format"] = "scaffold"
        assigned.add(id(best_scaffold))

    # 3. Everything else is text
    for a in articles:
        if "content_format" not in a:
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
        "---SLIDE_7---": "slide_7",
        "---SLIDE_8---": "slide_8",
        "---SLIDE_9---": "slide_9",
        "---SLIDE_10---": "slide_10",
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


def should_include_outsider_context(persona, category):
    """Only include the radio/OOH outsider context when it genuinely adds something."""
    if persona == "The Sales Realist":
        return True
    if category in ("Sales", "Behavioural Science"):
        return True
    return False


def get_format_prompt(content_format, persona, pillar_context, category=""):
    """Return the appropriate system prompt for the given content format."""
    outsider = OUTSIDER_CONTEXT if should_include_outsider_context(persona, category) else ""

    if content_format == "carousel":
        return CAROUSEL_PROMPT.format(pillar_context=pillar_context, outsider_context=outsider)
    elif content_format == "opinion":
        return OPINION_PROMPT.format(pillar_context=pillar_context, outsider_context=outsider)
    elif content_format == "scaffold":
        return SCAFFOLD_INTERVIEW_PROMPT.format(pillar_context=pillar_context, outsider_context=outsider)
    else:
        return DRAFT_SYSTEM_PROMPT.format(persona=persona, pillar_context=pillar_context, outsider_context=outsider)


def generate_single_draft(article, persona, content_format=None):
    """Generate one draft using Sonnet."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    fmt = content_format or article.get("content_format", "text")
    category = article.get("category", "")
    pillar_context = get_pillar_context(category)
    system = get_format_prompt(fmt, persona, pillar_context, category=category)

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

    max_tokens = 2048 if fmt == "carousel" else 1500 if fmt == "story_prompt" else 1024

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


def generate_original_draft():
    """Generate an original prompt draft that doesn't need a source article.

    This is the content that builds a personal brand - prompted from Russell's
    daily work, not from newsletter reactions.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Rotate prompt type based on day of week
    today = datetime.now().weekday()
    prompt_type = ORIGINAL_PROMPT_TYPES[today % len(ORIGINAL_PROMPT_TYPES)]

    prompt_type_descriptions = {
        "discovery_call": "DISCOVERY CALL MOMENT - What happened on a call this week that surprised you, confirmed something, or changed your mind?",
        "outbound_opinion": "OUTBOUND OBSERVATION - What's something you see other sellers doing that you'd never do? Or something you do that others think is wrong?",
        "ai_in_workflow": "AI IN YOUR WORKFLOW - What AI tool did you actually use this week? What worked? What didn't?",
        "side_project": "SIDE PROJECT LESSON - What are you building right now and what's it teaching you about sales, product, or customers?",
        "contrarian_take": "CONTRARIAN TAKE - What's a commonly accepted sales truth that you think is wrong?",
    }

    user_text = (
        f"Generate a writing prompt for Russell.\n\n"
        f"Prompt type for today: {prompt_type_descriptions.get(prompt_type, prompt_type)}\n\n"
        f"Make the questions specific and pointed enough to trigger a real memory or opinion."
    )

    logger.info(f"Generating original prompt (type: {prompt_type})")

    response = client.messages.create(
        model=SONNET_MODEL,
        max_tokens=1024,
        system=ORIGINAL_PROMPT_SYSTEM,
        messages=[{"role": "user", "content": user_text}],
    )

    raw = response.content[0].text
    draft = parse_draft(raw)
    draft["persona"] = "Original"
    draft["article"] = {
        "title": f"Original Prompt ({prompt_type.replace('_', ' ').title()})",
        "source": "Russell's daily work",
        "category": "Sales" if prompt_type in ("discovery_call", "outbound_opinion", "contrarian_take") else "AI" if prompt_type == "ai_in_workflow" else "Sales",
        "total_score": 0,
        "one_line_summary": f"Original content prompt: {prompt_type}",
    }
    draft["content_format"] = "original"
    return draft


def generate_drafts(articles, personas):
    """Generate drafts for all selected articles plus one original prompt."""
    drafts = []
    for article, persona in zip(articles, personas):
        try:
            draft = generate_single_draft(article, persona)
            drafts.append(draft)
        except Exception as e:
            logger.error(f"Failed to generate draft for '{article['title']}': {e}")
            continue

    # Generate the original prompt (no article needed)
    try:
        original = generate_original_draft()
        drafts.append(original)
    except Exception as e:
        logger.error(f"Failed to generate original prompt: {e}")

    return drafts
