"""One-time OAuth setup for Google Docs and Gmail APIs.

Run locally: python setup_google_auth.py
This will:
1. Open a browser for Google OAuth consent
2. Save token.json locally
3. Print the base64-encoded token for use as a GitHub Actions secret
"""
import base64
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def main():
    creds = None

    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    except FileNotFoundError:
        pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print(f"Token saved to {TOKEN_FILE}")

    # Print base64 for GitHub secret
    with open(TOKEN_FILE) as f:
        token_data = f.read()

    encoded = base64.b64encode(token_data.encode()).decode()
    print("\n--- Copy this value as your GOOGLE_CREDENTIALS GitHub secret ---")
    print(encoded)
    print("--- End ---")


if __name__ == "__main__":
    main()
