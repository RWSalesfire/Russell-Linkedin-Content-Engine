import logging
import os
from datetime import datetime

from config import GOOGLE_DOC_ID

logger = logging.getLogger(__name__)

# Colour palette (RGB 0-1 scale)
BLUE = {"red": 0.0, "green": 0.4, "blue": 0.8}
DARK_GREY = {"red": 0.42, "green": 0.46, "blue": 0.49}
GREEN = {"red": 0.16, "green": 0.65, "blue": 0.27}
AMBER_BG = {"red": 1.0, "green": 0.95, "blue": 0.8}


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
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "namedStyleType": "HEADING_1",
                "borderBottom": {
                    "color": {"color": {"rgbColor": BLUE}},
                    "width": {"magnitude": 2, "unit": "PT"},
                    "padding": {"magnitude": 6, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "spaceBelow": {"magnitude": 14, "unit": "PT"},
            },
            "fields": "namedStyleType,borderBottom,spaceBelow",
        }})
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {"foregroundColor": {"color": {"rgbColor": BLUE}}},
            "fields": "foregroundColor",
        }})

    def add_heading2(self, text):
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "namedStyleType": "HEADING_2",
                "borderLeft": {
                    "color": {"color": {"rgbColor": BLUE}},
                    "width": {"magnitude": 3, "unit": "PT"},
                    "padding": {"magnitude": 8, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
                "spaceAbove": {"magnitude": 16, "unit": "PT"},
            },
            "fields": "namedStyleType,borderLeft,spaceAbove",
        }})
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {"foregroundColor": {"color": {"rgbColor": BLUE}}},
            "fields": "foregroundColor",
        }})

    def add_bold(self, text):
        s, e = self._append(text)
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "textStyle": {"bold": True},
            "fields": "bold",
        }})

    def add_italic(self, text):
        s, e = self._append(text)
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "textStyle": {"italic": True},
            "fields": "italic",
        }})

    def add_grey(self, text):
        s, e = self._append(text)
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "textStyle": {
                "foregroundColor": {"color": {"rgbColor": DARK_GREY}},
                "fontSize": {"magnitude": 9, "unit": "PT"},
            },
            "fields": "foregroundColor,fontSize",
        }})

    def add_text(self, text):
        self._append(text)

    def add_post_block(self, text):
        """Add post content with green left border and italic styling."""
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {"italic": True},
            "fields": "italic",
        }})
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "indentStart": {"magnitude": 14, "unit": "PT"},
                "borderLeft": {
                    "color": {"color": {"rgbColor": GREEN}},
                    "width": {"magnitude": 3, "unit": "PT"},
                    "padding": {"magnitude": 8, "unit": "PT"},
                    "dashStyle": "SOLID",
                },
            },
            "fields": "indentStart,borderLeft",
        }})

    def add_recommendation(self, text):
        """Add recommendation with amber background."""
        s, e = self._append(text + "\n")
        self.format_requests.append({"updateParagraphStyle": {
            "range": {"startIndex": s, "endIndex": e},
            "paragraphStyle": {
                "shading": {
                    "backgroundColor": {"color": {"rgbColor": AMBER_BG}}
                },
                "indentStart": {"magnitude": 8, "unit": "PT"},
                "indentEnd": {"magnitude": 8, "unit": "PT"},
                "spaceAbove": {"magnitude": 4, "unit": "PT"},
                "spaceBelow": {"magnitude": 4, "unit": "PT"},
            },
            "fields": "shading.backgroundColor,indentStart,indentEnd,spaceAbove,spaceBelow",
        }})
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {"bold": True},
            "fields": "bold",
        }})

    def add_separator(self):
        """Add a thin styled separator line."""
        s, e = self._append("━" * 60 + "\n")
        self.format_requests.append({"updateTextStyle": {
            "range": {"startIndex": s, "endIndex": e - 1},
            "textStyle": {
                "foregroundColor": {"color": {"rgbColor": DARK_GREY}},
                "fontSize": {"magnitude": 5, "unit": "PT"},
            },
            "fields": "foregroundColor,fontSize",
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


def build_formatted_doc(drafts, category_distribution):
    """Build rich-formatted Google Docs API requests for the daily digest."""
    doc = DocBuilder()

    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y")

    # Title
    doc.add_heading1(f"Daily LinkedIn Drafts \u2014 {date_str}")
    doc.add_text("\n")

    # Sources summary
    doc.add_heading2("\U0001f4f0  Today's Sources")
    for draft in drafts:
        article = draft["article"]
        score = article.get("total_score", 0)
        doc.add_text(f"\u2022 {article['title']} ({article['source']}) \u2014 Score: {score}/50\n")
    doc.add_text("\n")
    doc.add_separator()

    # Each draft
    for i, draft in enumerate(drafts, 1):
        article = draft["article"]

        doc.add_heading2(
            f"Draft {i}  |  {draft['persona']}  |  {article.get('category', 'General')}"
        )
        doc.add_grey(f"Source: {article['title']} ({article['source']})\n")
        doc.add_text("\n")

        # Post content with green left border
        doc.add_post_block(draft["post"])
        doc.add_text("\n")

        # Alternative hooks
        doc.add_bold("Alternative Hooks:\n")
        doc.add_text(f"1. {draft['alt_hook_1']}\n")
        doc.add_text(f"2. {draft['alt_hook_2']}\n")
        doc.add_text("\n")

        # Image prompt
        doc.add_bold("Image Prompt: ")
        doc.add_grey(f"{draft['image_prompt']}\n")
        doc.add_text("\n")
        doc.add_separator()

    # Recommendation
    if drafts:
        best = max(drafts, key=lambda d: d["article"].get("total_score", 0))
        doc.add_heading2("\U0001f3af  Recommendation")
        doc.add_recommendation(
            f"Draft by {best['persona']} on \"{best['article']['title']}\" "
            f"\u2014 highest source score ({best['article'].get('total_score', 0)}/50)"
        )
        doc.add_text("\n")

    # Content balance
    doc.add_heading2("\U0001f4ca  Content Balance (Last 7 Days)")
    for cat, count in category_distribution.items():
        doc.add_text(f"\u2022 {cat}: {count} posts\n")
    doc.add_text("\n")
    doc.add_separator()
    doc.add_text("\n")

    return doc.build()


def format_drafts(drafts, category_distribution):
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
        lines.append(f"- {article['title']} ({article['source']}) - Score: {score}/50")
    lines.append("")
    lines.append("-" * 50)

    # Each draft
    for i, draft in enumerate(drafts, 1):
        article = draft["article"]
        lines.append("")
        lines.append(f"DRAFT {i} | {draft['persona']} | {article.get('category', 'General')}")
        lines.append(f"Source: {article['title']} ({article['source']})")
        lines.append("-" * 40)
        lines.append("")
        lines.append(draft["post"])
        lines.append("")
        lines.append("Alternative Hooks:")
        lines.append(f"1. {draft['alt_hook_1']}")
        lines.append(f"2. {draft['alt_hook_2']}")
        lines.append("")
        lines.append(f"Image Prompt: {draft['image_prompt']}")
        lines.append("-" * 40)

    # Recommendation
    lines.append("")
    if drafts:
        best = max(drafts, key=lambda d: d["article"].get("total_score", 0))
        lines.append(
            f"RECOMMENDATION: Draft by {best['persona']} on "
            f"\"{best['article']['title']}\" - highest source score "
            f"({best['article'].get('total_score', 0)}/50)"
        )

    # 7-day balance
    lines.append("")
    lines.append("CONTENT BALANCE (LAST 7 DAYS):")
    for cat, count in category_distribution.items():
        lines.append(f"- {cat}: {count} posts")

    lines.append("")
    lines.append("=" * 50)
    lines.append("")

    return "\n".join(lines)


def get_google_creds():
    """Load Google credentials from token file or base64 env var."""
    from gmail_feeds import get_google_creds as _get_creds
    return _get_creds()


def push_to_google_doc(drafts, category_distribution):
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
        requests = build_formatted_doc(drafts, category_distribution)

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


def output_drafts(drafts, category_distribution, dry_run=False):
    """Format and output drafts to Google Doc or fallback to markdown."""
    text = format_drafts(drafts, category_distribution)

    if dry_run:
        print(text)
        return text

    success = push_to_google_doc(drafts, category_distribution)
    if not success:
        logger.warning("Google Docs push failed, saving markdown fallback")
        save_markdown_fallback(text)

    return text
