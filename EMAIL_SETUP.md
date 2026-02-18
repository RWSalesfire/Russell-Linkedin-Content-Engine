# Gmail Email Integration Setup

The LinkedIn Content Engine now supports sending daily email digests in addition to Google Docs output.

## Features

- **Daily HTML Email Digest**: Professional formatted email with all 5 LinkedIn drafts
- **Email Recommendation**: Highlights the best draft based on source score
- **Content Balance Overview**: Shows category distribution from past 7 days
- **Graceful Fallback**: Email failures don't break the pipeline

## Setup Instructions

### 1. Re-authenticate Google OAuth

The Gmail send functionality requires additional OAuth scopes. You need to re-authenticate:

```bash
cd Russell-Linkedin-Content-Engine
python setup_google_auth.py
```

This will:
1. Open your browser for Google OAuth consent
2. Request additional Gmail send permissions
3. Save updated token.json locally
4. Print base64-encoded credentials for GitHub Actions

### 2. Update GitHub Actions Secret

Copy the base64 output from step 1 and update the `GOOGLE_CREDENTIALS` secret in GitHub repository settings.

### 3. Add Recipient Email

Add `RECIPIENT_EMAIL` as a new secret in GitHub repository settings with Russell's email address.

## Usage

### Command Line Options

```bash
# Normal pipeline (Google Docs + Email)
python main.py

# Dry run (preview only, no sends)
python main.py --dry-run

# Test email only (skip Google Docs)
python main.py --email-only

# Skip email (Google Docs only)
python main.py --no-email

# View newsletters only
python main.py --feeds-only
```

### Testing Email

Use the test script to verify email functionality:

```bash
python test_email.py
```

This will:
1. Run a dry-run test with sample data
2. Optionally send a real test email to verify setup

## Email Format

The email includes:
- **Header**: Date and branding
- **Source Summary**: List of articles with scores
- **5 Draft Sections**: Each with persona, post content, alternative hooks, and image prompt
- **Recommendation**: Highlights the best draft
- **Content Balance**: 7-day category distribution
- **Professional Styling**: Clean HTML format with fallback plain text

## Scheduling

The GitHub Actions workflow runs Monday-Friday at 6:00 AM UTC. The email is sent as part of the normal pipeline.

## Environment Variables

- `RECIPIENT_EMAIL`: Email address to send daily digest
- `GOOGLE_CREDENTIALS`: Base64-encoded OAuth token (existing, needs update for send scope)
- Other existing variables remain unchanged

## Troubleshooting

### Email Not Sending

1. Check that `RECIPIENT_EMAIL` is set in GitHub secrets
2. Verify Google OAuth has `gmail.send` scope (re-run `setup_google_auth.py`)
3. Check GitHub Actions logs for error details

### Permission Errors

1. Re-authenticate with `python setup_google_auth.py`
2. Update `GOOGLE_CREDENTIALS` GitHub secret with new token

### Email in Spam

Gmail API emails are generally trusted, but check spam folder on first run.

## Security

- Uses OAuth2 (no password storage)
- Same authentication as existing Google Docs integration
- Email content contains no sensitive data
- Respects Gmail API rate limits