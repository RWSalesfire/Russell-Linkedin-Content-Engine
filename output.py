import logging
import os
from datetime import datetime

from config import ENGAGEMENT_TARGETS, GOOGLE_DOC_ID

logger = logging.getLogger(__name__)

# Colour palette (RGB 0-1 scale)
CHARCOAL = {"red": 0.2, "green": 0.2, "blue": 0.2}
MID_GREY = {"red": 0.55, "green": 0.55, "blue": 0.55}
LIGHT_GREY = {"red": 0.85, "green": 0.85, "blue": 0.85}
TEAL = {"red": 0.0, "green": 0.59, "blue": 0.53}
TEAL_LIGHT = {"red": 0.91, "green": 0.97, "blue": 0.96}
AMBER = {"red": 0.85, "green": 0.55, "blue": 0.0}
AMBER_BG = {"red": 1.0, "green": 0.96, "blue": 0.88}
RED_BG = {"red": 1.0, "green": 0.93, "blue": 0.93}
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}


class DocBuilder:
    """Builds Google Docs API batchUpdate requests with rich formatting."""

    def __init__(self):
        self.cursor = 1  # Google Docs index starts at 1
        self.text_parts = []
        self.format_requests = []

    def _append(self, text):
        """Append text and return (start, end) indices."""
        start = self.cursor
        self.text_parts.append(text)
        self.cursor += len(text)
        return start, self.cursor

    def add_heading1(self, text):
        """Main title - large, dark, with subtle bottom border."""
        if not text:
            return
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "namedStyleType": "HEADING_1",
                "spaceBelow": {"magnitude": 8, "unit": "PT"},
            },
            "fields": "namedStyleType,spaceBelow",
        }})
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {
                "foregroundColor": {"color": {"rgbColor": CHARCOAL}},
                "fontSize": {"magnitude": 20, "unit": "PT"},
            },
            "fields": "foregroundColor,fontSize",
        }})

    def add_date_subtitle(self, text):
        """Date line below the title - grey, smaller."""
        if not text:
            return
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {
                "foregroundColor": {"color": {"rgbColor": MID_GREY}},
                "fontSize": {"magnitude": 11, "unit": "PT"},
            },
            "fields": "foregroundColor,fontSize",
        }})
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "spaceBelow": {"magnitude": 16, "unit": "PT"},
            },
            "fields": "spaceBelow",
        }})

    def add_section_heading(self, text):
        """Section heading - teal, uppercase feel, with left accent bar."""
        if not text:
            return
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "namedStyleType": "HEADING_3",
                "borderLeft": {
                    "color": {"color": {"rgbColor": TEAL}},
                    "width": {"magnitude": 4, "unit": "PT"},
                    "padding": {"magnitude": 10, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "spaceAbove": {"magnitude": 20, "unit": "PT"},
                "spaceBelow": {"magnitude": 8, "unit": "PT"},
            },
            "fields": "namedStyleType,borderLeft,spaceAbove,spaceBelow",
        }})
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {
                "foregroundColor": {"color": {"rgbColor": TEAL}},
                "bold": True,
                "fontSize": {"magnitude": 11, "unit": "PT"},
            },
            "fields": "foregroundColor,bold,fontSize",
        }})

    def add_draft_heading(self, draft_num, fmt, persona, category):
        """Draft header - clean card-style with teal background strip."""
        label = f"DRAFT {draft_num}"
        detail = f"  {fmt.upper()}  \u00b7  {persona}  \u00b7  {category}"
        s, e = self._append(label + detail + "\n")

        # Teal background strip
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "namedStyleType": "NORMAL_TEXT",
                "shading": {
                    "backgroundColor": {"color": {"rgbColor": TEAL_LIGHT}}
                },
                "indentStart": {"magnitude": 8, "unit": "PT"},
                "indentEnd": {"magnitude": 8, "unit": "PT"},
                "spaceAbove": {"magnitude": 24, "unit": "PT"},
                "spaceBelow": {"magnitude": 6, "unit": "PT"},
                "borderTop": {
                    "color": {"color": {"rgbColor": TEAL}},
                    "width": {"magnitude": 2, "unit": "PT"},
                    "padding": {"magnitude": 6, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
            },
            "fields": "namedStyleType,shading.backgroundColor,indentStart,indentEnd,spaceAbove,spaceBelow,borderTop",
        }})
        # "DRAFT N" in bold teal
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": s + len(label)},
            "textStyle": {
                "bold": True,
                "foregroundColor": {"color": {"rgbColor": TEAL}},
                "fontSize": {"magnitude": 12, "unit": "PT"},
            },
            "fields": "bold,foregroundColor,fontSize",
        }})
        # Detail in grey
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s + len(label), "endIndex": e - 1},
            "textStyle": {
                "foregroundColor": {"color": {"rgbColor": MID_GREY}},
                "fontSize": {"magnitude": 10, "unit": "PT"},
            },
            "fields": "foregroundColor,fontSize",
        }})

    def add_source_line(self, text):
        """Source attribution - small grey text."""
        if not text:
            return
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {
                "foregroundColor": {"color": {"rgbColor": MID_GREY}},
                "fontSize": {"magnitude": 9, "unit": "PT"},
                "italic": True,
            },
            "fields": "foregroundColor,fontSize,italic",
        }})
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "spaceBelow": {"magnitude": 10, "unit": "PT"},
                "indentStart": {"magnitude": 8, "unit": "PT"},
            },
            "fields": "spaceBelow,indentStart",
        }})

    def add_bold(self, text):
        if not text:
            return
        s, e = self._append(text)
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "textStyle": {
                "bold": True,
                "foregroundColor": {"color": {"rgbColor": CHARCOAL}},
            },
            "fields": "bold,foregroundColor",
        }})

    def add_label(self, text):
        """Small bold label - for 'Alternative Hooks:', 'Image Prompt:', etc."""
        if not text:
            return
        s, e = self._append(text)
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "textStyle": {
                "bold": True,
                "foregroundColor": {"color": {"rgbColor": MID_GREY}},
                "fontSize": {"magnitude": 9, "unit": "PT"},
            },
            "fields": "bold,foregroundColor,fontSize",
        }})

    def add_italic(self, text):
        if not text:
            return
        s, e = self._append(text)
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "textStyle": {"italic": True},
            "fields": "italic",
        }})

    def add_grey(self, text):
        if not text:
            return
        s, e = self._append(text)
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "textStyle": {
                "foregroundColor": {"color": {"rgbColor": MID_GREY}},
                "fontSize": {"magnitude": 9, "unit": "PT"},
            },
            "fields": "foregroundColor,fontSize",
        }})

    def add_text(self, text):
        self._append(text)

    def add_post_block(self, text):
        """Post content - normal weight, left border in teal, comfortable reading size."""
        if not text:
            return
        # Split into paragraphs and apply border to each
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {
                "foregroundColor": {"color": {"rgbColor": CHARCOAL}},
                "fontSize": {"magnitude": 11, "unit": "PT"},
            },
            "fields": "foregroundColor,fontSize",
        }})
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "indentStart": {"magnitude": 16, "unit": "PT"},
                "indentEnd": {"magnitude": 16, "unit": "PT"},
                "borderLeft": {
                    "color": {"color": {"rgbColor": TEAL}},
                    "width": {"magnitude": 3, "unit": "PT"},
                    "padding": {"magnitude": 12, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "lineSpacing": 130,
            },
            "fields": "indentStart,indentEnd,borderLeft,lineSpacing",
        }})

    def add_recommendation(self, text):
        """Recommendation callout - amber accent."""
        if not text:
            return
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "shading": {
                    "backgroundColor": {"color": {"rgbColor": AMBER_BG}}
                },
                "borderLeft": {
                    "color": {"color": {"rgbColor": AMBER}},
                    "width": {"magnitude": 4, "unit": "PT"},
                    "padding": {"magnitude": 10, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "indentStart": {"magnitude": 8, "unit": "PT"},
                "indentEnd": {"magnitude": 8, "unit": "PT"},
                "spaceAbove": {"magnitude": 8, "unit": "PT"},
                "spaceBelow": {"magnitude": 8, "unit": "PT"},
            },
            "fields": "shading.backgroundColor,borderLeft,indentStart,indentEnd,spaceAbove,spaceBelow",
        }})
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {
                "bold": True,
                "foregroundColor": {"color": {"rgbColor": CHARCOAL}},
                "fontSize": {"magnitude": 10, "unit": "PT"},
            },
            "fields": "bold,foregroundColor,fontSize",
        }})

    def add_story_prompt_block(self, text):
        """Story prompt - red-tinted callout to flag it needs input."""
        if not text:
            return
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "shading": {
                    "backgroundColor": {"color": {"rgbColor": RED_BG}}
                },
                "indentStart": {"magnitude": 16, "unit": "PT"},
                "indentEnd": {"magnitude": 16, "unit": "PT"},
                "lineSpacing": 130,
            },
            "fields": "shading.backgroundColor,indentStart,indentEnd,lineSpacing",
        }})

    def add_bullet(self, text):
        """A clean bullet point."""
        if not text:
            return
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {
                "foregroundColor": {"color": {"rgbColor": CHARCOAL}},
                "fontSize": {"magnitude": 10, "unit": "PT"},
            },
            "fields": "foregroundColor,fontSize",
        }})
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "indentStart": {"magnitude": 18, "unit": "PT"},
                "indentFirstLine": {"magnitude": 8, "unit": "PT"},
                "spaceBelow": {"magnitude": 2, "unit": "PT"},
            },
            "fields": "indentStart,indentFirstLine,spaceBelow",
        }})

    def add_separator(self):
        """Clean thin horizontal line."""
        s, e = self._append("\n")
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "borderBottom": {
                    "color": {"color": {"rgbColor": LIGHT_GREY}},
                    "width": {"magnitude": 0.5, "unit": "PT"},
                    "padding": {"magnitude": 12, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "spaceBelow": {"magnitude": 4, "unit": "PT"},
            },
            "fields": "borderBottom,spaceBelow",
        }})

    def build(self):
        """Return the full list of API requests."""
        full_text = "".join(self.text_parts)
        insert_request = {
            "insertText": {
                "location": {"index": 1},
                "text": full_text,
            }
        }
        return [insert_request] + self.format_requests


def get_todays_engagement_targets():
    """Return 5 engagement targets for today, rotating based on priority and day."""
    today = datetime.now().weekday()

    daily = [t for t in ENGAGEMENT_TARGETS if t["priority"] == "daily"]
    three_x = [t for t in ENGAGEMENT_TARGETS if t["priority"] == "3x_week"]
    weekly = [t for t in ENGAGEMENT_TARGETS if t["priority"] == "weekly"]

    targets = list(daily)  # always include daily targets

    # Rotate 3x_week targets: pick 2 based on day of week
    if three_x:
        start = (today * 2) % len(three_x)
        targets.append(three_x[start % len(three_x)])
        targets.append(three_x[(start + 1) % len(three_x)])

    # Add 1 weekly target on Mon/Wed/Fri
    if today in (0, 2, 4) and weekly:
        idx = (today // 2) % len(weekly)
        targets.append(weekly[idx])

    return targets[:8]


def format_draft_content(draft, doc_builder=None, plain_lines=None):
    """Render a single draft in the appropriate format. Works for both Doc and plain text."""
    content_format = draft.get("content_format", "text")

    if content_format == "carousel":
        _render_carousel(draft, doc_builder, plain_lines)
    elif content_format in ("scaffold", "original"):
        _render_scaffold(draft, doc_builder, plain_lines)
    elif content_format == "opinion":
        _render_opinion(draft, doc_builder, plain_lines)
    else:
        _render_text(draft, doc_builder, plain_lines)


def _render_text(draft, doc, lines):
    """Render standard text post."""
    if doc:
        doc.add_post_block(draft.get("post", ""))
        doc.add_text("\n")
        doc.add_label("ALTERNATIVE HOOKS\n")
        doc.add_bullet(f"1.  {draft.get('alt_hook_1', '')}")
        doc.add_bullet(f"2.  {draft.get('alt_hook_2', '')}")
        doc.add_text("\n")
        doc.add_label("IMAGE PROMPT\n")
        doc.add_grey(f"{draft.get('image_prompt', '')}\n")
    if lines is not None:
        lines.append(draft.get("post", ""))
        lines.append("")
        lines.append("Alternative Hooks:")
        lines.append(f"1. {draft.get('alt_hook_1', '')}")
        lines.append(f"2. {draft.get('alt_hook_2', '')}")
        lines.append("")
        lines.append(f"Image Prompt: {draft.get('image_prompt', '')}")


def _render_carousel(draft, doc, lines):
    """Render carousel slides."""
    slides = []
    for i in range(1, 11):
        slide = draft.get(f"slide_{i}", "")
        if slide:
            slides.append(slide)

    if doc:
        doc.add_label("CAROUSEL - Paste into aiCarousels.com\n")
        doc.add_text("\n")
        for i, slide in enumerate(slides, 1):
            doc.add_label(f"Slide {i}\n")
            doc.add_post_block(slide)
            doc.add_text("\n")
        caption = draft.get("caption", "")
        if caption:
            doc.add_label("LINKEDIN CAPTION\n")
            doc.add_post_block(caption)
    if lines is not None:
        lines.append("[CAROUSEL - Paste into aiCarousels.com]")
        lines.append("")
        for i, slide in enumerate(slides, 1):
            lines.append(f"  Slide {i}: {slide}")
            lines.append("")
        caption = draft.get("caption", "")
        if caption:
            lines.append(f"LinkedIn Caption: {caption}")


def _render_scaffold(draft, doc, lines):
    """Render scaffold interview prompt or original prompt with highlight."""
    scaffold = draft.get("story_scaffold", "")
    content_format = draft.get("content_format", "scaffold")

    label = "ORIGINAL POST PROMPT" if content_format == "original" else "SCAFFOLD - Pick an angle"

    if doc:
        doc.add_label(f"{label} - Needs Russell's input\n")
        doc.add_text("\n")
        doc.add_story_prompt_block(scaffold)
    if lines is not None:
        lines.append(f"[{label} - NEEDS RUSSELL'S INPUT]")
        lines.append("")
        lines.append(scaffold)


def _render_opinion(draft, doc, lines):
    """Render opinion/hot take post."""
    if doc:
        doc.add_label("HOT TAKE\n")
        doc.add_text("\n")
        doc.add_post_block(draft.get("post", ""))
        doc.add_text("\n")
        if draft.get("alt_hook_1"):
            doc.add_label("ALTERNATIVE HOOKS\n")
            doc.add_bullet(f"1.  {draft.get('alt_hook_1', '')}")
            doc.add_bullet(f"2.  {draft.get('alt_hook_2', '')}")
    if lines is not None:
        lines.append("[HOT TAKE]")
        lines.append("")
        lines.append(draft.get("post", ""))
        lines.append("")
        if draft.get("alt_hook_1"):
            lines.append("Alternative Hooks:")
            lines.append(f"1. {draft.get('alt_hook_1', '')}")
            lines.append(f"2. {draft.get('alt_hook_2', '')}")


def build_formatted_doc(drafts, category_distribution, format_distribution=None):
    """Build rich-formatted Google Docs API requests for the daily digest."""
    doc = DocBuilder()

    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y")

    # Title and date
    doc.add_heading1("Daily LinkedIn Drafts")
    doc.add_date_subtitle(date_str)
    doc.add_separator()

    # Sources summary
    doc.add_section_heading("TODAY'S SOURCES")
    for draft in drafts:
        article = draft["article"]
        score = article.get("total_score", 0)
        fmt = draft.get("content_format", "text")
        hook_score = draft.get("hook_score", "-")
        doc.add_bullet(f"[{fmt.upper()}]  {article['title']}  -  Score: {score}/70  |  Hook: {hook_score}")
    doc.add_text("\n")

    # Each draft
    for i, draft in enumerate(drafts, 1):
        article = draft["article"]
        fmt = draft.get("content_format", "text")
        composite = draft.get("composite_score", "-")

        doc.add_draft_heading(i, fmt, draft.get("persona", ""), article.get("category", "General"))
        doc.add_source_line(f"Source: {article['title']} ({article['source']})  |  Composite: {composite}")

        # Format-specific rendering
        format_draft_content(draft, doc_builder=doc)

        doc.add_text("\n")

    doc.add_separator()

    # Recommendation (weighted scoring)
    if drafts:
        best = max(drafts, key=lambda d: d.get("composite_score", 0))
        doc.add_section_heading("RECOMMENDATION")
        doc.add_recommendation(
            f"Draft by {best.get('persona', '')} [{best.get('content_format', 'text').upper()}] on \"{best['article']['title']}\" "
            f"- composite score {best.get('composite_score', 0)} (article: {best['article'].get('total_score', 0)}/70, hook: {best.get('hook_score', 0)}/100)"
        )
        doc.add_text("\n")

    # Content balance
    doc.add_section_heading("CONTENT BALANCE  (Last 7 Days)")
    for cat, count in category_distribution.items():
        doc.add_bullet(f"{cat}: {count} posts")
    if format_distribution:
        doc.add_text("\n")
        doc.add_label("FORMAT DISTRIBUTION\n")
        for fmt, count in format_distribution.items():
            doc.add_bullet(f"{fmt}: {count}")
    doc.add_text("\n")

    # Engagement plan
    doc.add_section_heading("TODAY'S ENGAGEMENT PLAN")
    targets = get_todays_engagement_targets()
    doc.add_label("Comment on these accounts BEFORE posting:\n")
    for t in targets:
        doc.add_bullet(f"{t['name']}  ({t['niche']})  [{t['priority']}]")
    doc.add_text("\n")
    doc.add_grey("Reminder: Reply to every comment within 60 minutes of posting.\n")
    doc.add_text("\n")

    return doc.build()


def format_drafts(drafts, category_distribution, format_distribution=None):
    """Format all drafts as plain text for console output."""
    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y")

    lines = []
    lines.append("=" * 50)
    lines.append(f"  {date_str} - Daily LinkedIn Drafts")
    lines.append("=" * 50)
    lines.append("")

    # Source summary
    lines.append("TODAY'S SOURCES:")
    for draft in drafts:
        article = draft["article"]
        score = article.get("total_score", 0)
        fmt = draft.get("content_format", "text")
        hook_score = draft.get("hook_score", "-")
        lines.append(f"- [{fmt.upper()}] {article['title']} ({article['source']}) - Score: {score}/70 | Hook: {hook_score}")
    lines.append("")
    lines.append("-" * 50)

    # Each draft
    for i, draft in enumerate(drafts, 1):
        article = draft["article"]
        fmt = draft.get("content_format", "text")
        composite = draft.get("composite_score", "-")
        lines.append("")
        lines.append(f"DRAFT {i} | {fmt.upper()} | {draft.get('persona', '')} | {article.get('category', 'General')} | Composite: {composite}")
        lines.append(f"Source: {article['title']} ({article['source']})")
        lines.append("-" * 40)
        lines.append("")

        # Format-specific rendering
        format_draft_content(draft, plain_lines=lines)

        lines.append("")
        lines.append("-" * 40)

    # Recommendation
    lines.append("")
    if drafts:
        best = max(drafts, key=lambda d: d.get("composite_score", 0))
        lines.append(
            f"RECOMMENDATION: [{best.get('content_format', 'text').upper()}] Draft by {best.get('persona', '')} on "
            f"\"{best['article']['title']}\" - composite score {best.get('composite_score', 0)} "
            f"(article: {best['article'].get('total_score', 0)}/70, hook: {best.get('hook_score', 0)}/100)"
        )

    # 7-day balance
    lines.append("")
    lines.append("CONTENT BALANCE (LAST 7 DAYS):")
    for cat, count in category_distribution.items():
        lines.append(f"- {cat}: {count} posts")
    if format_distribution:
        lines.append("")
        lines.append("FORMAT DISTRIBUTION:")
        for fmt, count in format_distribution.items():
            lines.append(f"- {fmt}: {count}")

    # Engagement plan
    lines.append("")
    lines.append("=" * 50)
    lines.append("TODAY'S ENGAGEMENT PLAN")
    lines.append("=" * 50)
    targets = get_todays_engagement_targets()
    lines.append("Comment on these accounts BEFORE posting:")
    for t in targets:
        lines.append(f"- {t['name']} ({t['niche']}) [{t['priority']}]")
    lines.append("")
    lines.append("Reminder: Reply to every comment within 60 minutes of posting.")

    lines.append("")
    lines.append("=" * 50)
    lines.append("")

    return "\n".join(lines)


def get_google_creds():
    """Load Google credentials from token file or base64 env var."""
    from gmail_feeds import get_google_creds as _get_creds
    return _get_creds()


def push_to_google_doc(drafts, category_distribution, format_distribution=None):
    """Push richly formatted drafts to Google Doc."""
    from googleapiclient.discovery import build

    creds = get_google_creds()
    if not creds:
        logger.error("No Google credentials available")
        return False

    if not GOOGLE_DOC_ID:
        logger.error("GOOGLE_DOC_ID not set")
        return False

    try:
        service = build("docs", "v1", credentials=creds)
        requests = build_formatted_doc(drafts, category_distribution, format_distribution)

        service.documents().batchUpdate(
            documentId=GOOGLE_DOC_ID,
            body={"requests": requests},
        ).execute()

        logger.info("Successfully pushed formatted drafts to Google Doc")
        return True

    except Exception as e:
        logger.error(f"Failed to push to Google Doc: {e}")
        return False


def save_markdown_fallback(text):
    """Save output as markdown file in output/ directory."""
    os.makedirs("output", exist_ok=True)
    filename = f"output/drafts_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.md"
    with open(filename, "w") as f:
        f.write(text)
    logger.info(f"Saved fallback output to {filename}")
    return filename


def output_drafts(drafts, category_distribution, format_distribution=None, dry_run=False):
    """Format and output drafts to Google Doc or fallback to markdown."""
    text = format_drafts(drafts, category_distribution, format_distribution)

    # Generate carousel PDFs for any carousel drafts
    for draft in drafts:
        if draft.get("content_format") == "carousel":
            try:
                from carousel_builder import build_carousel_pdf
                pdf_path = build_carousel_pdf(draft)
                if pdf_path:
                    draft["carousel_pdf"] = pdf_path
                    logger.info(f"Carousel PDF generated: {pdf_path}")
                    if dry_run:
                        print(f"\nCarousel PDF: {pdf_path}")
            except Exception as e:
                logger.warning(f"Carousel PDF generation failed (non-fatal): {e}")

    if dry_run:
        print(text)
        return text

    success = push_to_google_doc(drafts, category_distribution, format_distribution)
    if not success:
        logger.warning("Google Docs push failed, saving markdown fallback")
        save_markdown_fallback(text)

    # Sync to Obsidian vault (non-fatal)
    try:
        from obsidian_output import sync_post_log, update_content_calendar, write_story_scaffold
        sync_post_log(drafts, datetime.now())
        update_content_calendar(drafts, datetime.now())
        for draft in drafts:
            if draft.get("content_format") in ("scaffold", "original"):
                write_story_scaffold(draft)
    except Exception as e:
        logger.warning(f"Obsidian sync failed (non-fatal): {e}")

    return text
