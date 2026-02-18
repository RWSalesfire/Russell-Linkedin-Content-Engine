#!/usr/bin/env python3
"""Test script for email sending functionality."""
import logging
from datetime import datetime

from email_sender import send_daily_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

# Sample test data
sample_drafts = [
    {
        "persona": "The Honest AI User",
        "post": "I've been testing AI tools for 6 months now.\n\nMost promise everything, deliver frustration.\n\nBut here's what actually works:\n\n→ Claude for writing (not perfect, but consistent)\n→ Midjourney for quick mockups\n→ Notion AI for meeting notes\n\nThe pattern? Simple tasks, clear prompts, human oversight.\n\nAI isn't magic. It's a very smart intern.\n\nTreat it like one.",
        "alt_hook_1": "Every AI tool claims to be revolutionary.",
        "alt_hook_2": "I wasted £200 on AI subscriptions last month.",
        "image_prompt": "Split screen showing frustrated person vs organized workspace with AI tools",
        "article": {
            "title": "The Reality of AI Tool ROI in 2026",
            "source": "AI Trends Weekly",
            "category": "AI",
            "total_score": 42
        }
    },
    {
        "persona": "The eCommerce Observer",
        "post": "Watched 50+ checkout processes this week.\n\n90% fail at the same point: trust.\n\nNot the payment security (everyone's got SSL).\nNot the design (Shopify templates work fine).\n\nIt's the little things:\n\n❌ No delivery timeframes\n❌ Hidden shipping costs\n❌ No customer reviews visible\n❌ Checkout feels rushed\n\nTrust is built in details, not declarations.",
        "alt_hook_1": "Your checkout page is leaking revenue.",
        "alt_hook_2": "I abandoned 12 carts this week. Here's why.",
        "image_prompt": "Split checkout comparison showing trust signals vs missing elements",
        "article": {
            "title": "eCommerce Conversion Killers: What 2026 Data Shows",
            "source": "RetailWeek",
            "category": "eCommerce",
            "total_score": 38
        }
    },
    {
        "persona": "The Sales Realist",
        "post": "Discovery calls are broken.\n\nNot because reps ask bad questions.\n\nBecause prospects give rehearsed answers.\n\nEveryone knows 'the script' now:\n\n\"What's your biggest challenge?\"\n\"How are you handling X currently?\"\n\"What would success look like?\"\n\nProspects have heard these 100 times.\n\nTry this instead: \"What's working well that you'd hate to lose?\"\n\nWatch their guard drop.",
        "alt_hook_1": "Your discovery questions aren't discovering anything.",
        "alt_hook_2": "Prospects are better at discovery calls than you are.",
        "image_prompt": "Two people in conversation, one looking engaged vs one looking bored",
        "article": {
            "title": "Why Modern Sales Discovery Is Failing",
            "source": "Sales Hacker",
            "category": "Sales",
            "total_score": 44
        }
    },
    {
        "persona": "The Human",
        "post": "My 4-year-old asked me why adults make everything so complicated.\n\nI was explaining why we can't just \"buy the nice biscuits\" every time we shop.\n\nThen I realised: I spend hours debating email sequences that could just say \"Hi, this might help you.\"\n\nWe overcomplicate because we're scared of being too simple.\n\nBut simple works.\n\nMy daughter gets more excited about a cardboard box than the expensive toy that came in it.\n\nMaybe we should ask: what's our cardboard box?",
        "alt_hook_1": "Adults overcomplicate everything. Kids don't.",
        "alt_hook_2": "My daughter taught me something about marketing this week.",
        "image_prompt": "Parent and child playing with simple cardboard box, expensive toys ignored in background",
        "article": {
            "title": "The Psychology of Simplicity in Consumer Behavior",
            "source": "Behavioral Economics Review",
            "category": "Behavioural Science",
            "total_score": 41
        }
    },
    {
        "persona": "The eCommerce Observer",
        "post": "Klaviyo's new predictive analytics dashboard launched yesterday.\n\nEveryone's raving about the AI predictions.\n\nI tested it on 3 client accounts.\n\nThe predictions? Impressive.\nThe actionable insights? Disappointing.\n\n\"Customer X will spend £200 next month\" - great.\n\"Send them this exact email on Tuesday at 2pm\" - even better.\n\nBut that second bit isn't there yet.\n\nPrediction without prescription is just expensive fortune telling.",
        "alt_hook_1": "Klaviyo's new AI is impressive but incomplete.",
        "alt_hook_2": "Predictive analytics that don't predict actions are useless.",
        "image_prompt": "Split screen: crystal ball vs actionable dashboard interface, showing prediction vs prescription",
        "article": {
            "title": "Klaviyo Launches Advanced Predictive Analytics Suite",
            "source": "Email Marketing Weekly",
            "category": "Email Marketing",
            "total_score": 46
        }
    }
]

sample_category_distribution = {
    "AI": 2,
    "eCommerce": 1,
    "Sales": 2,
    "AI in Sales": 1,
    "Email Marketing": 0,
    "Behavioural Science": 1
}

def main():
    print("Testing email functionality...")
    print("=" * 50)

    # Test in dry-run mode first
    print("1. Testing dry-run mode:")
    success = send_daily_digest(
        sample_drafts,
        sample_category_distribution,
        recipient_email="test@example.com",
        dry_run=True
    )

    if success:
        print("✅ Dry-run test passed!")
    else:
        print("❌ Dry-run test failed!")

    print("\n" + "=" * 50)

    # Ask user if they want to send a real email
    while True:
        send_real = input("Send a real test email? (y/n): ").lower().strip()
        if send_real in ['y', 'yes']:
            email = input("Enter recipient email address: ").strip()
            if email:
                print(f"Sending test email to {email}...")
                success = send_daily_digest(
                    sample_drafts,
                    sample_category_distribution,
                    recipient_email=email,
                    dry_run=False
                )

                if success:
                    print("✅ Email sent successfully!")
                else:
                    print("❌ Email sending failed! Check logs for details.")
            break
        elif send_real in ['n', 'no']:
            print("Skipping real email send.")
            break
        else:
            print("Please enter 'y' or 'n'")

if __name__ == "__main__":
    main()