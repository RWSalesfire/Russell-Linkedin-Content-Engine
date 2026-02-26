import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Google Docs
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

# Email configuration
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# Model IDs
HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-5-20250929"

# Pipeline settings
LOOKBACK_HOURS = 24
DRAFT_COUNT = 5
WORD_RANGE = (100, 150)
DEDUP_THRESHOLD = 0.65
MAX_RETRIES = 1

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

Avoid AI-sounding language:
- BANNED words (never use): delve, intricate, tapestry, pivotal, underscore, landscape, foster, testament, enhance, crucial, comprehensive, multifaceted, nuanced, groundbreaking, cutting-edge, game-changer, paradigm, synergy, realm, beacon, cornerstone
- No "It's not X, it's Y" or "This isn't about X. It's about Y." negative parallelism constructions
- Never use em dashes (—). Use commas, full stops, or restructure
- No wrap-up phrases: "Overall,", "In conclusion,", "In summary,", "Ultimately,"  — just end the post
- No inflated symbolism: "serves as a testament", "plays a vital role", "watershed moment", "stands as a", "leaves a lasting impact", "deeply rooted"
- No editorialising filler: "it's important to note", "it's worth mentioning", "no discussion would be complete without"
- No overused transitions: "moreover", "furthermore", "in addition", "in contrast", "on the other hand", "consequently". Start a new line or use a short punchy transition instead
- No dangling -ing commentary: "ensuring greater efficiency", "highlighting the importance", "reflecting a broader trend", "emphasising the need"
- No vague attribution: "industry experts say", "observers have noted", "some critics argue". Name the source or state it directly
- No false ranges: "from X to Y" constructions that don't represent a genuine spectrum

Russell's natural phrases (use sparingly and naturally):
- "to be honest"
- "don't get me wrong"
- "basically"
- "from that perspective"
- "brilliant" (as agreement)"""

# Content calendar rules
MAX_SAME_CATEGORY_STREAK = 2
MAX_SAME_PERSONA_STREAK = 3
HISTORY_LOOKBACK_DAYS = 7
SOURCE_COOLDOWN_POSTS = 3
