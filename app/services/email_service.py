"""Email delivery for account verification."""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from urllib.parse import quote

from app.core.config import settings

logger = logging.getLogger("smartcampus.email")


def build_email_verification_link(token: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/login?verify_token={quote(token, safe='')}"


def send_email_verification_email(nom: str, email: str, token: str) -> bool:
    if not settings.smtp_configured:
        logger.error("SMTP is not configured; verification email was not sent.")
        return False

    link = build_email_verification_link(token)
    message = EmailMessage()
    message["Subject"] = f"{settings.APP_NAME} - Verify your email"
    message["From"] = formataddr((settings.SMTP_FROM_NAME, settings.SMTP_FROM_EMAIL))
    message["To"] = email
    message.set_content(
        f"Hello {nom},\n\nVerify your email address to activate your account:\n{link}\n\n"
        f"This link expires in {settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours."
    )

    try:
        context = ssl.create_default_context()
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
                context=context,
            )
        else:
            server = smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
            )
        with server:
            server.ehlo()
            if not settings.SMTP_USE_SSL and settings.SMTP_USE_STARTTLS:
                server.starttls(context=context)
                server.ehlo()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
    except (smtplib.SMTPException, OSError, ValueError) as exc:
        logger.error("Verification email delivery failed: %s", type(exc).__name__)
        return False

    logger.info("Verification email accepted by SMTP server.")
    return True
