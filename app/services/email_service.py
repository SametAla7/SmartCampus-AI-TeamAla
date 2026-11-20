"""Service - Envoi d'emails via SMTP (verification, bienvenue, reinitialisation).

- Si SMTP n'est pas configure, aucun email n'est envoye : l'evenement est journalise.
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
        '<!doctype html><html lang="fr"><head><meta charset="utf-8"></head>'
        '<body style="margin:0;padding:32px 16px;background:#f3f6fb;'
        'font-family:Arial,Helvetica,sans-serif;color:#1f2937">'
        '<div style="max-width:560px;margin:0 auto;background:#fff;border:1px solid #e5eaf2;'
        'border-radius:16px;overflow:hidden">'
        '<div style="padding:24px 32px;background:#123b73;color:#fff">'
        f'<p style="margin:0;font-size:13px;letter-spacing:1.5px;font-weight:bold">{escape(settings.APP_NAME)}</p>'
        '</div><div style="padding:32px">'
        f'<h1 style="margin:0 0 20px;font-size:24px;color:#123b73">{escape(title)}</h1>'
        f'{body_html}'
        '<hr style="border:0;border-top:1px solid #e5eaf2;margin:28px 0 18px">'
        '<p style="margin:0;color:#718096;font-size:12px;line-height:1.6">'
        'Vous recevez cet email à la suite d’une demande effectuée sur SmartCampus AI. '
        'Si vous n’êtes pas à l’origine de cette demande, vous pouvez ignorer ce message.'
        '</p></div></div></body></html>'
    )


def build_email_verification_link(token: str) -> str:
    return f"{settings.FRONTEND_URL}/login?verify_token={quote(token, safe='')}"


def send_email_verification_email(nom: str, email: str, token: str) -> bool:
    link = build_email_verification_link(token)
    hours = settings.EMAIL_VERIFICATION_EXPIRE_HOURS
    subject = f"{settings.APP_NAME} - Confirmez votre adresse email"
    text = (
        f"Bonjour {nom},\n\n"
        f"Merci d'avoir rejoint {settings.APP_NAME}. Confirmez votre adresse email "
        f"pour activer votre compte :\n{link}\n\n"
        f"Ce lien expire dans {hours} heures. Si vous n'avez pas créé de compte, "
        "ignorez simplement cet email.\n"
    )
    html = _html_layout(
        "Bienvenue parmi nous !",
        f'<p style="font-size:16px;line-height:1.7">Bonjour {escape(nom)},</p>'
        '<p style="font-size:15px;line-height:1.7;color:#4b5563">'
        'Merci de rejoindre SmartCampus AI. Pour sécuriser votre compte et accéder à votre espace, '
        'confirmez votre adresse email en cliquant ci-dessous.</p>'
        f'<p style="margin:28px 0"><a href="{escape(link)}" '
        'style="display:inline-block;background:#1760d4;color:#fff;padding:14px 22px;'
        'border-radius:8px;text-decoration:none;font-weight:bold">Confirmer mon adresse email</a></p>'
        f'<p style="font-size:13px;line-height:1.6;color:#718096">Ce lien est valable {hours} heures. '
        'Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :</p>'
        f'<p style="font-size:12px;line-height:1.6;word-break:break-all;color:#1760d4">{escape(link)}</p>',
    )
    return send_email(email, subject, text, html)


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
