import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def _send_smtp(message: EmailMessage) -> None:
    """Synchronous SMTP sender run via asyncio thread pool."""
    try:
        with smtplib.SMTP(host=settings.SMTP_HOST, port=settings.SMTP_PORT, timeout=5) as server:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
            logger.info("Email sent successfully to %s", message["To"])
    except Exception as exc:
        logger.warning("Failed to send email to %s via Mailpit: %s", message["To"], exc)


async def send_email(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    await asyncio.to_thread(_send_smtp, msg)


async def send_verification_email(to_email: str, token: str) -> None:
    subject = "OpportunityAbroad: Verify Your Email"
    verify_url = f"http://localhost:5173/verify-email?token={token}"
    text_content = f"Please verify your email address by following this link: {verify_url}\n\nToken: {token}"
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Welcome to OpportunityAbroad!</h2>
        <p>Please confirm your email address by clicking the button below:</p>
        <p><a href="{verify_url}" style="background-color: #16a34a; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Verify Email</a></p>
        <p>Or copy this verification code into the application:</p>
        <pre style="background: #f1f5f9; padding: 10px; border-radius: 4px;">{token}</pre>
      </body>
    </html>
    """
    await send_email(to_email, subject, html_content, text_content)


async def send_password_reset_email(to_email: str, token: str) -> None:
    subject = "OpportunityAbroad: Reset Your Password"
    reset_url = f"http://localhost:5173/reset-password?token={token}"
    text_content = (
        f"You requested a password reset. Follow this link to set a new password: {reset_url}\n\nToken: {token}"
    )
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Password Reset Request</h2>
        <p>You recently requested to reset your password for OpportunityAbroad.</p>
        <p><a href="{reset_url}" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
        <p>This link expires in 1 hour. If you did not request this, please ignore this email.</p>
      </body>
    </html>
    """
    await send_email(to_email, subject, html_content, text_content)


async def send_deadline_reminder_email(to_email: str, opportunity_title: str, days_remaining: int) -> None:
    """Send a minimal reminder without logging or embedding personal data."""
    subject = f"OpportunityAbroad: {days_remaining}-day deadline reminder"
    text_content = (
        f"Your saved opportunity '{opportunity_title}' has an application deadline in "
        f"{days_remaining} days. Please review your application."
    )
    html_content = (
        "<html><body><p>Deadline reminder</p>"
        f"<p><strong>{opportunity_title}</strong> has an application deadline in "
        f"{days_remaining} days.</p></body></html>"
    )
    await send_email(to_email, subject, html_content, text_content)
