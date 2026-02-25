"""Email sending functionality for daily LinkedIn drafts digest."""
import base64
import html
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from googleapiclient.discovery import build

from config import RECIPIENT_EMAIL

logger = logging.getLogger(__name__)


def get_google_creds_with_send():
    """Load Google credentials with Gmail send access."""
    from gmail_feeds import get_google_creds
    return get_google_creds()


def create_html_email_template(drafts, category_distribution):
    """Create professional HTML email template for daily digest."""
    now = datetime.now()
    date_str = now.strftime("%A, %d %B %Y")

    # Find the best draft (highest score)
    best_draft = max(drafts, key=lambda d: d["article"].get("total_score", 0)) if drafts else None

    # Generate source list with scores (escape user-supplied data to prevent HTML injection)
    sources_html = ""
    for i, draft in enumerate(drafts, 1):
        article = draft["article"]
        score = article.get("total_score", 0)
        title = html.escape(article['title'])
        source = html.escape(article['source'])
        sources_html += f"    <li><strong>{title}</strong> ({source}) - Score: {score}/50</li>\n"

    # Generate drafts HTML
    drafts_html = ""
    for i, draft in enumerate(drafts, 1):
        article = draft["article"]

        # Format post content with line breaks (escape first, then add <br>)
        post_content = html.escape(draft["post"]).replace("\n", "<br>")
        persona = html.escape(draft['persona'])
        category = html.escape(article.get('category', 'General'))
        title = html.escape(article['title'])
        source = html.escape(article['source'])
        alt_hook_1 = html.escape(draft['alt_hook_1'])
        alt_hook_2 = html.escape(draft['alt_hook_2'])
        image_prompt = html.escape(draft['image_prompt'])

        drafts_html += f"""
    <div class="draft">
        <h2>Draft {i}: {persona} | {category}</h2>
        <p class="source"><strong>Source:</strong> {title} ({source})</p>
        <div class="post-content">
            {post_content}
        </div>
        <div class="alt-hooks">
            <p><strong>Alternative Hooks:</strong></p>
            <ol>
                <li>{alt_hook_1}</li>
                <li>{alt_hook_2}</li>
            </ol>
        </div>
        <div class="image-prompt">
            <p><strong>Image Prompt:</strong> {image_prompt}</p>
        </div>
    </div>
    """

    # Generate recommendation
    recommendation_html = ""
    if best_draft:
        best_persona = html.escape(best_draft['persona'])
        best_title = html.escape(best_draft['article']['title'])
        best_score = best_draft['article'].get('total_score', 0)
        recommendation_html = f"""
    <div class="recommendation">
        <h2>🎯 Recommendation</h2>
        <p><strong>Draft by {best_persona}</strong> on "{best_title}" - highest source score ({best_score}/50)</p>
    </div>
    """

    # Generate content balance
    balance_html = ""
    for cat, count in category_distribution.items():
        balance_html += f"    <li>{html.escape(cat)}: {count} posts</li>\n"

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Daily LinkedIn Drafts - {date_str}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}

        .email-container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #0066cc;
            text-align: center;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}

        h2 {{
            color: #0066cc;
            border-left: 4px solid #0066cc;
            padding-left: 15px;
            margin-top: 30px;
        }}

        .draft {{
            background-color: #f8f9fa;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 4px solid #28a745;
        }}

        .post-content {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            font-style: italic;
            border: 1px solid #dee2e6;
        }}

        .alt-hooks, .image-prompt {{
            margin: 15px 0;
            padding: 10px;
            background-color: #e9ecef;
            border-radius: 3px;
        }}

        .source {{
            color: #6c757d;
            font-size: 0.9em;
            margin: 10px 0;
        }}

        .recommendation {{
            background-color: #fff3cd;
            padding: 20px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}

        ul, ol {{
            padding-left: 20px;
        }}

        li {{
            margin: 8px 0;
        }}

        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            color: #6c757d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <h1>Daily LinkedIn Drafts - {date_str}</h1>

        <h2>📰 Today's Sources</h2>
        <ul>
{sources_html}        </ul>

{drafts_html}

{recommendation_html}

        <h2>📊 Content Balance (Last 7 Days)</h2>
        <ul>
{balance_html}        </ul>

        <div class="footer">
            <p>Generated by Russell's LinkedIn Content Engine<br>
            <small>Powered by Claude AI and Gmail API</small></p>
        </div>
    </div>
</body>
</html>"""

    return html_content


def send_daily_digest(drafts, category_distribution, recipient_email=None, dry_run=False):
    """Send daily LinkedIn drafts digest email."""
    if not recipient_email:
        recipient_email = RECIPIENT_EMAIL

    if not recipient_email:
        logger.warning("No recipient email configured. Skipping email send.")
        return False

    if dry_run:
        logger.info(f"DRY RUN: Would send email to {recipient_email}")
        html_content = create_html_email_template(drafts, category_distribution)
        print("\n--- EMAIL PREVIEW ---")
        print(f"To: {recipient_email}")
        print(f"Subject: Daily LinkedIn Drafts - {datetime.now().strftime('%d %B %Y')}")
        print("--- HTML CONTENT ---")
        print(html_content[:500] + "...[truncated]")
        print("--- END PREVIEW ---\n")
        return True

    try:
        creds = get_google_creds_with_send()
        if not creds:
            logger.error("No Google credentials with send access available")
            return False

        service = build('gmail', 'v1', credentials=creds)

        # Create the email
        now = datetime.now()
        subject = f"Daily LinkedIn Drafts - {now.strftime('%d %B %Y')}"
        html_content = create_html_email_template(drafts, category_distribution)

        # Create MIME message
        message = MIMEMultipart('alternative')
        message['to'] = recipient_email
        message['subject'] = subject

        # Create HTML part
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)

        # Create plain text fallback
        plain_text = f"""Daily LinkedIn Drafts - {now.strftime('%A, %d %B %Y')}

TODAY'S SOURCES:
"""
        for i, draft in enumerate(drafts, 1):
            article = draft["article"]
            score = article.get("total_score", 0)
            plain_text += f"- {article['title']} ({article['source']}) - Score: {score}/50\n"

        plain_text += "\n" + "="*50 + "\n\n"

        for i, draft in enumerate(drafts, 1):
            article = draft["article"]
            plain_text += f"DRAFT {i} | {draft['persona']} | {article.get('category', 'General')}\n"
            plain_text += f"Source: {article['title']} ({article['source']})\n"
            plain_text += "-" * 40 + "\n\n"
            plain_text += draft["post"] + "\n\n"
            plain_text += "Alternative Hooks:\n"
            plain_text += f"1. {draft['alt_hook_1']}\n"
            plain_text += f"2. {draft['alt_hook_2']}\n\n"
            plain_text += f"Image Prompt: {draft['image_prompt']}\n"
            plain_text += "-" * 40 + "\n\n"

        # Add recommendation
        if drafts:
            best = max(drafts, key=lambda d: d["article"].get("total_score", 0))
            plain_text += f"RECOMMENDATION: Draft by {best['persona']} on "
            plain_text += f'"{best["article"]["title"]}" - highest source score '
            plain_text += f'({best["article"].get("total_score", 0)}/50)\n\n'

        # Add content balance
        plain_text += "CONTENT BALANCE (LAST 7 DAYS):\n"
        for cat, count in category_distribution.items():
            plain_text += f"- {cat}: {count} posts\n"

        plain_part = MIMEText(plain_text, 'plain')
        message.attach(plain_part)

        # Encode and send
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        send_message = {'raw': raw_message}

        result = service.users().messages().send(
            userId='me',
            body=send_message
        ).execute()

        logger.info(f"Email sent successfully to {recipient_email}. Message ID: {result['id']}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False