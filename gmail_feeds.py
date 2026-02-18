import base64
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import GOOGLE_CREDENTIALS_PATH, GOOGLE_TOKEN_PATH, LOOKBACK_HOURS

logger = logging.getLogger(__name__)


def load_newsletters_config(path="newsletters_config.json"):
    """Load newsletter configuration mapping senders to sources."""
    with open(path) as f:
        return json.load(f)["newsletters"]


def get_google_creds():
    """Load Google credentials with Gmail and Docs access."""
    SCOPES = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send"
    ]

    # CI path: base64-encoded credentials in env var
    b64_creds = os.getenv("GOOGLE_CREDENTIALS")
    if b64_creds:
        print(f"DEBUG: Base64 length: {len(b64_creds)}")
        print(f"DEBUG: Base64 first 50 chars: {b64_creds[:50]}")
        try:
            token_data = base64.b64decode(b64_creds).decode()
            print(f"DEBUG: Decoded length: {len(token_data)}")
            print(f"DEBUG: Decoded first 100 chars: {token_data[:100]}")
            token_dict = json.loads(token_data)
        except Exception as e:
            print(f"DEBUG: Error during decoding/parsing: {e}")
            print(f"DEBUG: Full decoded data: {repr(token_data)}")
            raise
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


def extract_email_content(payload):
    """Extract text content from email payload, handling multipart messages."""
    content = ""

    if payload.get('parts'):
        # Multipart message
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
            elif part['mimeType'] == 'text/html':
                data = part['body'].get('data')
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    # Convert HTML to text
                    soup = BeautifulSoup(html_content, 'html.parser')
                    content = soup.get_text('\n', strip=True)
                    break
    else:
        # Single part message
        if payload['mimeType'] == 'text/plain':
            data = payload['body'].get('data')
            if data:
                content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif payload['mimeType'] == 'text/html':
            data = payload['body'].get('data')
            if data:
                html_content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                soup = BeautifulSoup(html_content, 'html.parser')
                content = soup.get_text('\n', strip=True)

    return content


def clean_email_content(content, subject):
    """Clean email content by removing headers, footers, and noise."""
    lines = content.split('\n')
    cleaned_lines = []

    # Remove common email noise patterns
    noise_patterns = [
        r'unsubscribe',
        r'view.*browser',
        r'forward.*friend',
        r'©.*rights reserved',
        r'privacy policy',
        r'manage.*preferences',
        r'update.*profile',
        r'^--$',
        r'^\s*$'  # empty lines
    ]

    skip_line = False
    for line in lines:
        line = line.strip()

        # Skip lines matching noise patterns
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in noise_patterns):
            continue

        # Skip very short lines (likely navigation/UI elements)
        if len(line) < 10:
            continue

        cleaned_lines.append(line)

    # Join and limit content length
    cleaned_content = '\n'.join(cleaned_lines)

    # Limit to reasonable length (newsletters can be very long)
    if len(cleaned_content) > 5000:
        cleaned_content = cleaned_content[:5000] + "..."

    return cleaned_content


def match_sender_to_newsletter(sender_email, newsletters_config):
    """Match sender email to newsletter configuration."""
    sender_email = sender_email.lower()

    for newsletter in newsletters_config:
        for pattern in newsletter['sender_patterns']:
            if pattern.lower() in sender_email:
                return newsletter

    # Default if no match found
    return {
        "name": f"Unknown Newsletter ({sender_email})",
        "category_hint": "General"
    }


def fetch_newsletter_emails(cutoff, newsletters_config):
    """Fetch emails with 'Newsletters' label from Gmail API."""
    creds = get_google_creds()
    if not creds:
        logger.error("No Google credentials available")
        return []

    try:
        service = build('gmail', 'v1', credentials=creds)

        # Convert cutoff to Gmail query format
        cutoff_str = cutoff.strftime('%Y/%m/%d')

        # Search for emails with Newsletters label after cutoff date
        query = f'label:newsletters after:{cutoff_str}'

        logger.info(f"Gmail query: {query}")

        # Get message IDs
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=100
        ).execute()

        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} newsletter emails")

        articles = []

        for message in messages:
            try:
                # Get full message details
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                # Extract headers
                headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                subject = headers.get('Subject', 'No Subject')
                sender = headers.get('From', 'Unknown Sender')
                date_str = headers.get('Date', '')

                # Parse date
                try:
                    # Gmail date format is typically RFC 2822
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(date_str)
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                except:
                    pub_date = datetime.now(timezone.utc)

                # Skip if before cutoff
                if pub_date < cutoff:
                    continue

                # Extract content
                content = extract_email_content(msg['payload'])
                cleaned_content = clean_email_content(content, subject)

                # Match sender to newsletter config
                newsletter = match_sender_to_newsletter(sender, newsletters_config)

                # Create article object in same format as RSS feeds
                article = {
                    "title": subject,
                    "summary": cleaned_content[:200] + "..." if len(cleaned_content) > 200 else cleaned_content,
                    "content": cleaned_content,
                    "url": f"gmail:{message['id']}",  # Gmail-specific URL
                    "published": pub_date.isoformat(),
                    "source": newsletter["name"],
                    "category_hint": newsletter["category_hint"],
                    "sender": sender
                }

                articles.append(article)
                logger.info(f"Processed: {subject} from {newsletter['name']}")

            except Exception as e:
                logger.warning(f"Failed to process message {message['id']}: {e}")
                continue

        return articles

    except Exception as e:
        logger.error(f"Failed to fetch Gmail newsletters: {e}")
        return []


def fetch_all_newsletters(config_path="newsletters_config.json"):
    """Fetch all newsletter emails and return articles from the last LOOKBACK_HOURS."""
    newsletters_config = load_newsletters_config(config_path)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    logger.info(f"Fetching newsletters since {cutoff.isoformat()}")

    articles = fetch_newsletter_emails(cutoff, newsletters_config)

    logger.info(f"Total newsletter articles fetched: {len(articles)}")
    return articles