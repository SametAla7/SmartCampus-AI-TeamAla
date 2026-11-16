"""Service - Envoi d'emails via SMTP (bienvenue, reinitialisation de mot de passe).

- Si SMTP n'est pas configure, aucun email n'est envoye : l'evenement est journalise
  (et en environnement de developpement, le contenu est affiche dans les logs pour
  pouvoir tester le parcours sans serveur SMTP).
- Les erreurs d'envoi ne font jamais echouer une requete API : `send_email` renvoie
  simplement False. Les identifiants SMTP ne sont jamais journalises.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from urllib.parse import quote

from app.core.config import settings

logger = logging.getLogger("smartcampus.email")


def send_email(to: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    """Envoie un email. Retourne True si le serveur SMTP l'a accepte."""
    if not settings.smtp_configured:
        logger.warning("SMTP non configure : email '%s' vers %s non envoye.", subject, to)
        if settings.APP_ENV == "development":
            logger.info("[DEV] Contenu de l'email vers %s :\n%s", to, text_body)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.SMTP_FROM_NAME, settings.SMTP_FROM_EMAIL))
    message["To"] = to
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    try:
        context = ssl.create_default_context()
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(
                settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT_SECONDS, context=context
            )
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT_SECONDS)
        with server:
            server.ehlo()
            if not settings.SMTP_USE_SSL and settings.SMTP_USE_STARTTLS:
                server.starttls(context=context)
                server.ehlo()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
        logger.info("Email '%s' envoye a %s.", subject, to)
        return True
    except (smtplib.SMTPException, OSError, ValueError) as exc:
        # Ne jamais journaliser les identifiants ; le type d'erreur suffit au diagnostic.
        logger.error("Echec d'envoi de l'email '%s' vers %s : %s", subject, to, type(exc).__name__)
        return False


def _html_layout(title: str, body_html: str) -> str:
    return (
        '<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#1f2937">'
        f'<h2 style="color:#1d4ed8">{escape(title)}</h2>{body_html}'
        '<hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">'
        f'<p style="font-size:12px;color:#6b7280">{escape(settings.APP_NAME)}</p></div>'
    )


def send_welcome_email(nom: str, email: str) -> bool:
    subject = f"Bienvenue sur {settings.APP_NAME}"
    text = (
        f"Bonjour {nom},\n\n"
        f"Votre compte {settings.APP_NAME} a bien ete cree.\n"
        f"Vous pouvez vous connecter ici : {settings.FRONTEND_URL}/login\n"
    )
    html = _html_layout(
        "Bienvenue !",
        f"<p>Bonjour {escape(nom)},</p><p>Votre compte a bien ete cree.</p>"
        f'<p><a href="{escape(settings.FRONTEND_URL)}/login">Se connecter</a></p>',
    )
    return send_email(email, subject, text, html)


def build_password_reset_link(token: str) -> str:
    return f"{settings.FRONTEND_URL}/reset-password?token={quote(token, safe='')}"


def send_password_reset_email(nom: str, email: str, token: str) -> bool:
    link = build_password_reset_link(token)
    minutes = settings.PASSWORD_RESET_EXPIRE_MINUTES
    subject = f"{settings.APP_NAME} - Reinitialisation de votre mot de passe"
    text = (
        f"Bonjour {nom},\n\n"
        "Une reinitialisation de mot de passe a ete demandee pour votre compte.\n"
        f"Ce lien est valable {minutes} minutes et ne peut servir qu'une fois :\n{link}\n\n"
        "Si vous n'etes pas a l'origine de cette demande, ignorez simplement cet email.\n"
    )
    html = _html_layout(
        "Reinitialisation du mot de passe",
        f"<p>Bonjour {escape(nom)},</p>"
        f"<p>Cliquez sur le bouton ci-dessous pour choisir un nouveau mot de passe. "
        f"Le lien est valable {minutes} minutes et ne peut servir qu'une fois.</p>"
        f'<p><a href="{escape(link)}" style="background:#1d4ed8;color:#fff;padding:10px 18px;'
        'border-radius:6px;text-decoration:none">Reinitialiser mon mot de passe</a></p>'
        "<p>Si vous n'etes pas a l'origine de cette demande, ignorez cet email.</p>",
    )
    return send_email(email, subject, text, html)
