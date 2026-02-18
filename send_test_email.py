#!/usr/bin/env python3
"""Send a real test email with sample data."""
import os
import sys
from test_email import sample_drafts, sample_category_distribution
from email_sender import send_daily_digest

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 send_test_email.py your.email@example.com")
        print("Example: python3 send_test_email.py russell@salesfire.co.uk")
        sys.exit(1)

    email = sys.argv[1]
    print(f"🧪 Testing email functionality...")
    print(f"📧 Recipient: {email}")
    print("=" * 50)

    # First show dry-run preview
    print("1. 📋 Dry-run preview:")
    dry_success = send_daily_digest(sample_drafts, sample_category_distribution, recipient_email=email, dry_run=True)

    if not dry_success:
        print("❌ Dry-run failed!")
        sys.exit(1)

    print("\n" + "=" * 50)

    # Ask for confirmation
    confirm = input("\n📤 Send real email now? (y/n): ").lower().strip()

    if confirm != 'y' and confirm != 'yes':
        print("📋 Test cancelled. No email sent.")
        sys.exit(0)

    # Send real email
    print("\n2. 📧 Sending real email...")
    real_success = send_daily_digest(sample_drafts, sample_category_distribution, recipient_email=email, dry_run=False)

    if real_success:
        print("🎉 SUCCESS! Email sent successfully!")
        print(f"📬 Check your inbox: {email}")
        print("📱 Don't forget to check spam folder if you don't see it")
    else:
        print("❌ FAILED! Email could not be sent.")
        print("🔍 Check the error messages above for details")

if __name__ == "__main__":
    main()