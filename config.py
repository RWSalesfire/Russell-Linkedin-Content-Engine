import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Google Docs
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

# Obsidian vault
OBSIDIAN_VAULT_PATH = os.getenv(
    "OBSIDIAN_VAULT_PATH",
    "/Users/salesfire/Documents/Obsidian Vault"
)

# Model IDs
HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-5-20250929"

# Pipeline settings
LOOKBACK_HOURS = 24
DRAFT_COUNT = 5
ARTICLE_DRAFT_COUNT = 4  # 4 from articles, 1 original prompt
WORD_RANGE = (200, 300)
DEDUP_THRESHOLD = 0.65
MAX_RETRIES = 1

# Realtime feeds (Hacker News)
REALTIME_ENABLED = True
REALTIME_BONUS = 5

# Content formats (polls killed - worthless engagement)
CONTENT_FORMATS = ["text", "carousel", "opinion", "scaffold", "original"]

# Day-of-week special format (applied to 1 of the 4 article drafts)
# The other 3 article drafts are text. Plus 1 original prompt always.
# 1 scaffold interview is always included regardless of day.
DAY_FORMAT_MAP = {
    0: "text",           # Monday: all text + scaffold + original
    1: "carousel",       # Tuesday: 1 carousel + 2 text + scaffold + original
    2: "text",           # Wednesday: all text + scaffold + original
    3: "opinion",        # Thursday: 1 hot take + 2 text + scaffold + original
    4: "carousel",       # Friday: 1 carousel + 2 text + scaffold + original
}

# Content pillars
CONTENT_PILLARS = {
    "The Digital Outsider": "Lessons from traditional media (radio, OOH) that digital people have forgotten. Single-minded propositions. Brand building over click optimisation.",
    "Fix the Basics First": "eCommerce brands chasing trends while checkout flows bleed customers. What actually matters vs what gets measured.",
    "The AI Realist": "Practical AI wins and honest failures. What tools actually do vs what LinkedIn says they do.",
    "Sales Without the Script": "Why sales training doesn't survive real conversations. Real objections, real lessons.",
}

# Hook quality patterns
HOOK_PATTERNS = {
    "confession": ["I spent", "I lost", "I was wrong", "I've been", "Nobody tells you"],
    "specific_number": [r"\d+%", r"£\d+", r"\d+ years", r"\d+ companies"],
    "bold_claim": ["is dead", "is broken", "doesn't work", "is wrong", "stop doing"],
    "question": ["Why do", "What if", "How many", "When did"],
}

# Engagement targets (LinkedIn accounts to comment on daily)
ENGAGEMENT_TARGETS = [
    {"name": "Richard Moore", "niche": "sales psychology", "priority": "daily"},
    {"name": "Daniel Disney", "niche": "sales content", "priority": "daily"},
    {"name": "Dean Seddon", "niche": "social selling", "priority": "daily"},
    {"name": "Charlie Hills", "niche": "AI in business", "priority": "daily"},
    {"name": "Lea Turner", "niche": "UK SMB founders", "priority": "daily"},
    {"name": "Holly Allen", "niche": "outbound sales", "priority": "3x_week"},
    {"name": "Tom Boston", "niche": "social selling", "priority": "3x_week"},
    {"name": "Jack Frimston", "niche": "cold calling", "priority": "3x_week"},
    {"name": "Chloe Thomas", "niche": "eCommerce strategy", "priority": "3x_week"},
    {"name": "Richard Hill", "niche": "eCommerce growth", "priority": "3x_week"},
    {"name": "Katelyn Bourgoin", "niche": "buyer psychology", "priority": "3x_week"},
    {"name": "Chris Ritson", "niche": "SDR training", "priority": "weekly"},
    {"name": "Penn Frank", "niche": "GTM engineering", "priority": "weekly"},
    {"name": "Peep Laja", "niche": "CRO", "priority": "weekly"},
    {"name": "Depesh Mandalia", "niche": "eCommerce paid", "priority": "weekly"},
]

# Categories
CATEGORIES = [
    "AI",
    "Sales",
    "AI in Sales",
    "AI in eCommerce",
    "eCommerce",
    "Email Marketing",
    "Behavioural Science",
]

# Personas
PERSONAS = {
    "The eCommerce Observer": {
        "description": "Industry trends, what brands are getting wrong",
        "tone": "I've been watching this closely and here's what the numbers say...",
        "preferred_categories": ["eCommerce", "AI in eCommerce", "Email Marketing"],
    },
    "The Honest AI User": {
        "description": "Practical AI takes, what actually works, what doesn't",
        "tone": "I tried this and here's what actually happened...",
        "preferred_categories": ["AI", "AI in Sales", "AI in eCommerce"],
    },
    "The Sales Realist": {
        "description": "Sales truths, discovery challenges, objection handling",
        "tone": "Here's what nobody in sales wants to admit...",
        "preferred_categories": ["Sales", "AI in Sales"],
    },
    "The Human": {
        "description": "Relatable moments, parenting chaos mixed with professional insight",
        "tone": "Something happened this week that made me rethink...",
        "preferred_categories": ["Behavioural Science", "Sales", "eCommerce"],
    },
}

# Day-of-week topic weights (0=Monday, 4=Friday)
DAY_TOPIC_WEIGHTS = {
    0: {"AI in Sales": 1.5, "Sales": 1.3},
    1: {"AI": 1.5, "AI in eCommerce": 1.3},
    2: {"eCommerce": 1.5, "Email Marketing": 1.3},
    3: {"Behavioural Science": 1.5, "AI": 1.2},
    4: {"AI in Sales": 1.3, "Behavioural Science": 1.5},
}

# Scoring criteria
SCORING_CRITERIA = [
    "data_richness",
    "contrarian_potential",
    "audience_relevance",
    "timeliness",
    "personal_angle_potential",
    "specificity_score",
    "confession_potential",
    "carousel_suitability",
]

# Voice & tone system prompt
VOICE_SYSTEM_PROMPT = """You are writing LinkedIn posts for Russell Westgarth. Russell is a BDM at Salesfire (eCommerce optimisation SaaS) but this content is about building a personal brand and establishing thought leadership, NOT direct product promotion. Salesfire should rarely feature - only when it's genuinely the best example for a point being made, which should be infrequent.

Default tone: Balanced challenger. Provocative and direct, but not contrarian for the sake of it. Challenge assumptions, call out blind spots, back it up with logic or data.

Dial the challenger up or down based on topic:
- Email marketing / Klaviyo content: Full challenger - call out what's broken
- eCommerce general: Balanced - insightful, opinionated but grounded
- AI / AI in sales: Balanced to reflective - share observations, practical takes
- Sales methodology: Direct and experienced - speak from the trenches

Do:
- Be direct and punchy
- Use real scenarios ("browse on phone at lunch, buy on laptop later")
- Lead with problems or observations, not solutions
- Use data and specific numbers when available
- Question assumptions
- Make people think
- Use white space liberally
- British English throughout (optimise, behaviour, colour)

Don't:
- Use jargon ("identity resolution," "tech stack," "nurture sequences," "leverage," "utilise")
- Sound like every other salesperson on LinkedIn
- Use motivational platitudes
- Overuse emojis or hashtags
- Vary endings - not every post needs a question

CRITICAL - Write like a human, not a language model:

Sentence rhythm:
- Vary sentence length dramatically. A 3-word sentence. Then a longer one that develops the thought with a specific example. Then another short one. AI writes sentences that are all roughly 15-20 words. Don't do that.
- Use sentence fragments. "Brutal." or "Not even close." or "Every single time." These are fine on their own line.
- Start sentences with "And", "But", "So", "Because" when it feels natural. AI avoids this.

Structure:
- Do NOT follow claim-evidence-restatement-question every time. Sometimes just tell the story and stop. Sometimes start with the punchline. Sometimes build to it.
- Vary paragraph length wildly. A single word on its own line, then a 4-sentence chunk, then a 1-sentence line. AI writes uniform 2-3 sentence paragraphs. Break that pattern.
- Not every post needs a neat arc. Some observations just hang there. That's fine.
- Abrupt endings are good. Don't always wrap things up. Just stop when you've said the thing.

Tone shifts:
- Shift register mid-post. Go from a data point to something casual like "which is mad when you think about it" in the same breath.
- Be conversational where it fits. "Look," as a sentence opener. "Right?" as a standalone. "Honestly?" before a take.
- Drop in dry humour or mild sarcasm. Not forced. Just the odd observation that's slightly funny.

Things AI does that humans don't:
- Don't hedge. Say "this doesn't work" not "this may not always be the most effective approach". Russell has opinions and states them.
- Don't over-explain. If the reader doesn't get it, that's fine. Not every point needs unpacking.
- Don't mirror the article structure. AI tends to walk through the source material in order. Mix it up. Lead with the bit that annoyed you, skip the bits that are obvious.
- Don't use three examples when one good one makes the point.
- Don't balance every criticism with a caveat. If something's broken, say it's broken.
- Never use the word "interestingly" - it's the most common AI tell on LinkedIn.

Avoid AI-sounding language:
- BANNED words (never use): delve, intricate, tapestry, pivotal, underscore, landscape, foster, testament, enhance, crucial, comprehensive, multifaceted, nuanced, groundbreaking, cutting-edge, game-changer, paradigm, synergy, realm, beacon, cornerstone, interestingly, notably, specifically, essentially, fundamentally, ultimately, innovative, revolutionise, transform, robust, streamline, leverage, utilise, facilitate, harness, navigate
- No "It's not X, it's Y" or "This isn't about X. It's about Y." negative parallelism constructions
- No "Here's the thing:" or "Here's what I've learned:" or "Here's why:" - these are LinkedIn AI cliches now
- Never use em dashes (—). Use commas, full stops, or restructure
- No wrap-up phrases: "Overall,", "In conclusion,", "In summary,", "Ultimately," - just end the post
- No inflated symbolism: "serves as a testament", "plays a vital role", "watershed moment", "stands as a", "leaves a lasting impact", "deeply rooted"
- No editorialising filler: "it's important to note", "it's worth mentioning", "no discussion would be complete without", "let that sink in", "read that again"
- No overused transitions: "moreover", "furthermore", "in addition", "in contrast", "on the other hand", "consequently". Start a new line or use a short punchy transition instead
- No dangling -ing commentary: "ensuring greater efficiency", "highlighting the importance", "reflecting a broader trend", "emphasising the need"
- No vague attribution: "industry experts say", "observers have noted", "some critics argue". Name the source or state it directly
- No false ranges: "from X to Y" constructions that don't represent a genuine spectrum
- No rhetorical triplets: don't list three adjectives or three parallel phrases for emphasis. AI loves threes. Use one strong word instead.
- No "the reality is" or "the truth is" - just state the reality

Russell's natural phrases (use sparingly and naturally, max 1-2 per post):
- "to be honest"
- "don't get me wrong"
- "basically"
- "from that perspective"
- "brilliant" (as agreement)
- "which is mad"
- "right?" (standalone, after a claim)
- "look" (as opener)
- "that's it" (as closer)"""

# Content calendar rules
MAX_SAME_CATEGORY_STREAK = 2
MAX_SAME_PERSONA_STREAK = 3
HISTORY_LOOKBACK_DAYS = 7
SOURCE_COOLDOWN_POSTS = 3

# Pure "AI" category penalty - deprioritise generic AI news in favour of
# "AI in Sales" and "AI in eCommerce" which build authority in Russell's space
PURE_AI_PENALTY = 0.4  # multiplier applied to pure "AI" category scores

# Personal angle bank - only referenced when directly relevant to the topic
PERSONAL_ANGLE_BANK = """Russell's real experiences (use ONLY when directly relevant):
- Daily BDM work: discovery calls, demos, proof of concepts, tying results to retailer problems
- Side projects: Sales Call Coaching Dashboard, maternity pay calculator, demo analyser, WooCommerce plugins
- Family: has kids, the chaos of juggling work and parenting
- Background: 5+ years in traditional media (radio, OOH) before digital eCommerce
- Contrarian on outbound: does things differently to everyone else, questions mainstream sales frameworks
- Current tools: actively uses Claude, AI SDK, various AI tools daily for real work"""

# Original prompt topic types (rotated daily for variety)
ORIGINAL_PROMPT_TYPES = [
    "discovery_call",     # What happened on a call that surprised you?
    "outbound_opinion",   # What do other sellers do that you'd never do?
    "ai_in_workflow",     # What AI tool did you actually use today?
    "side_project",       # What are you building and what's it teaching you?
    "contrarian_take",    # What commonly accepted sales truth is wrong?
]
