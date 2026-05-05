"""
Email utilities for HandyBridge.
Falls back to console output if MAIL_USERNAME is not configured — useful for local testing.
"""

from flask import current_app
from flask_mail import Message
from utils.extensions import mail


def send_reset_email(to_email: str, reset_url: str) -> None:
    """Send a password reset email to the given address."""
    subject = "HandyBridge — Password Reset Request"
    body = (
        "You requested a password reset for your HandyBridge account.\n\n"
        "Click the link below to reset your password (expires in 1 hour):\n"
        f"{reset_url}\n\n"
        "If you did not request this, you can safely ignore this email.\n"
    )

    try:
        msg = Message(subject=subject, recipients=[to_email], body=body)
        mail.send(msg)
    except Exception:
        # Print to console so the link is usable during local development
        current_app.logger.warning(
            "Flask-Mail is not configured — printing reset link to console."
        )
        print(f"\n{'='*60}")
        print(f"[PASSWORD RESET EMAIL]")
        print(f"To:      {to_email}")
        print(f"Subject: {subject}")
        print(f"\n{body}")
        print(f"{'='*60}\n")
