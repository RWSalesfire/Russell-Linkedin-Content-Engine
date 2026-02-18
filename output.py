import base64
import json
import logging
import os
from datetime import datetime

from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_DOC_ID, GOOGLE_TOKEN_PATH

logger = logging.getLogger(__name__)


def format_drafts(drafts, category_distribution):
    """Format all drafts into the doc/markdown template."""
    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y")

    lines = []
    lines.append("=" * 50)
    lines.append(f"  {date_str} - Daily LinkedIn Drafts")
    lines.append("=" * 50)
    lines.append("")

    # Source summary
    lines.append("TODAY'S SOURCES:")
    for i, draft in enumerate(drafts, 1):
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
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    SCOPES = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send"
    ]

    # CI path: base64-encoded credentials in env var
    b64_creds = os.getenv("GOOGLE_CREDENTIALS")
    if b64_creds:
        # Strip whitespace and handle potential double-encoding
        b64_creds = b64_creds.strip()
        # First base64 decode
        first_decode = base64.b64decode(b64_creds).decode().strip()

        # Check if we need to decode again (if it starts with base64 characters)
        if first_decode.startswith('eyJ'):  # Looks like base64 JSON
            # Second base64 decode
            token_data = base64.b64decode(first_decode).decode().strip()
        else:
            token_data = first_decode

        token_dict = json.loads(token_data)
        creds = Credentials.from_authorized_user_info(token_dict, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds

    # Local path: token.json file
    token_path = GOOGLE_TOKEN_PATH
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds

    return None


def push_to_google_doc(text):
    """Prepend formatted text to the Google Doc at index 1."""
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

        # Insert at index 1 (after the very first character position) to prepend
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": text + "\n\n",
                }
            }
        ]

        service.documents().batchUpdate(
            documentId=GOOGLE_DOC_ID,
            body={"requests": requests},
        ).execute()

        logger.info("Successfully pushed drafts to Google Doc")
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

    success = push_to_google_doc(text)
    if not success:
        logger.warning("Google Docs push failed, saving markdown fallback")
        save_markdown_fallback(text)

    return text
