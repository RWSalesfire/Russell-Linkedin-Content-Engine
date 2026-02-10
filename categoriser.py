import json
import logging

import anthropic

from config import ANTHROPIC_API_KEY, CATEGORIES, HAIKU_MODEL, SCORING_CRITERIA

logger = logging.getLogger(__name__)

CATEGORISE_SYSTEM_PROMPT = """You are a content analyst for a LinkedIn content strategist who writes about AI, Sales, and eCommerce. Your job is to categorise and score news articles.

For each article, you must:
1. Assign exactly ONE category from this list: {categories}
   The "category_hint" from the source is a suggestion but not binding.

2. Score the article on these criteria (1-10 each):
   - data_richness: Does it contain specific data, statistics, or research?
   - contrarian_potential: Could this fuel a take that challenges conventional wisdom?
   - audience_relevance: How relevant to eCommerce founders and sales leaders?
   - timeliness: Is this breaking/trending news vs evergreen?
   - personal_angle_potential: Could a personal story or opinion be woven in?

3. Write a one-line summary (max 20 words) capturing the key insight.

Return your response as a JSON array. Each element:
{{
  "article_index": <number matching the article number>,
  "category": "<category>",
  "scores": {{
    "data_richness": <1-10>,
    "contrarian_potential": <1-10>,
    "audience_relevance": <1-10>,
    "timeliness": <1-10>,
    "personal_angle_potential": <1-10>
  }},
  "one_line_summary": "<summary>"
}}

Return ONLY valid JSON. No commentary before or after."""


def build_articles_text(articles):
    """Format articles into a numbered list for the prompt."""
    parts = []
    for i, article in enumerate(articles):
        snippet = (article.get("content") or article.get("summary") or "")[:500]
        parts.append(
            f"Article {i}:\n"
            f"Title: {article['title']}\n"
            f"Source: {article['source']}\n"
            f"Category Hint: {article['category_hint']}\n"
            f"Content: {snippet}\n"
        )
    return "\n---\n".join(parts)


def categorise_and_score(articles):
    """Send all articles to Haiku in one batch call for categorisation and scoring."""
    if not articles:
        return articles

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system_prompt = CATEGORISE_SYSTEM_PROMPT.format(
        categories=", ".join(CATEGORIES)
    )
    user_text = build_articles_text(articles)

    logger.info(f"Sending {len(articles)} articles to Haiku for categorisation")

    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_text}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

    try:
        results = json.loads(raw)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse Haiku response as JSON:\n{raw[:500]}")
        # Assign defaults so pipeline can continue
        for article in articles:
            article["category"] = article.get("category_hint", "AI")
            article["scores"] = {c: 5 for c in SCORING_CRITERIA}
            article["total_score"] = 25
            article["one_line_summary"] = article["title"][:80]
        return sorted(articles, key=lambda a: a["total_score"], reverse=True)

    # Merge results back into article dicts
    results_by_index = {r["article_index"]: r for r in results}

    for i, article in enumerate(articles):
        result = results_by_index.get(i)
        if result:
            article["category"] = result["category"]
            article["scores"] = result["scores"]
            article["total_score"] = sum(result["scores"].values())
            article["one_line_summary"] = result.get("one_line_summary", "")
        else:
            article["category"] = article.get("category_hint", "AI")
            article["scores"] = {c: 5 for c in SCORING_CRITERIA}
            article["total_score"] = 25
            article["one_line_summary"] = article["title"][:80]

    articles.sort(key=lambda a: a["total_score"], reverse=True)
    logger.info(f"Top article: {articles[0]['title']} (score: {articles[0]['total_score']})")
    return articles
