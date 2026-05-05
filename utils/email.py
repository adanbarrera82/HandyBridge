"""
Email utilities for HandyBridge.
Uses Resend API for sending emails.
"""

from flask import current_app
import os
import requests


def send_reset_email(to_email: str, reset_url: str) -> None:
    """Send a password reset email using Resend API."""
    subject = "HandyBridge — Password Reset Request"
    body = (
        "You requested a password reset for your HandyBridge account.\n\n"
        "Click the link below to reset your password (expires in 1 hour):\n"
        f"{reset_url}\n\n"
        "If you did not request this, you can safely ignore this email.\n"
    )

    resend_api_key = os.environ.get('RESEND_API_KEY')
    
    if not resend_api_key:
        # Fall back to console
        current_app.logger.warning("Resend API key not configured — printing reset link to console.")
        print(f"\n{'='*60}")
        print(f"[PASSWORD RESET EMAIL]")
        print(f"To:      {to_email}")
        print(f"Subject: {subject}")
        print(f"\n{body}")
        print(f"{'='*60}\n")
        return

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "onboarding@resend.dev",
                "to": [to_email],
                "subject": subject,
                "text": body
            }
        )
        
        if response.status_code == 200:
            print("✓ Email sent successfully via Resend!")
        else:
            raise Exception(f"Resend API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        current_app.logger.error(f"Failed to send email via Resend: {e}")
        print(f"\n{'='*60}")
        print(f"[EMAIL ERROR: {e}]")
        print(f"[PASSWORD RESET EMAIL - Printing to console]")
        print(f"To:      {to_email}")
        print(f"Subject: {subject}")
        print(f"\n{body}")
        print(f"{'='*60}\n")