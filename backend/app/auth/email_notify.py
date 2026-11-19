"""Notify admin of pending signups (Resend or SMTP). Soft-fail if unconfigured."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


def notify_admin_pending_user(
    *,
    username: str,
    email: str,
    settings: Settings | None = None,
) -> dict:
    settings = settings or get_settings()
    admin = settings.admin_email.strip()
    subject = f"[Personality Playground] Pending approval: {username}"
    body = (
        f"A new user requested access.\n\n"
        f"Username: {username}\n"
        f"Email: {email}\n"
        f"Status: pending\n\n"
        f"Approve them in the Admin allowlist UI.\n"
        f"App: {settings.app_base_url}\n"
    )

    if settings.resend_api_key.strip():
        try:
            resp = httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.smtp_from,
                    "to": [admin],
                    "subject": subject,
                    "text": body,
                },
                timeout=15.0,
            )
            if resp.status_code >= 400:
                logger.warning("Resend failed: %s %s", resp.status_code, resp.text)
                return {"sent": False, "provider": "resend", "error": resp.text}
            return {"sent": True, "provider": "resend"}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Resend error: %s", exc)
            return {"sent": False, "provider": "resend", "error": str(exc)}

    if settings.smtp_host.strip():
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = settings.smtp_from
            msg["To"] = admin
            msg.set_content(body)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
            return {"sent": True, "provider": "smtp"}
        except Exception as exc:  # noqa: BLE001
            logger.warning("SMTP error: %s", exc)
            return {"sent": False, "provider": "smtp", "error": str(exc)}

    logger.info("Admin notify (no email provider): %s <%s>", username, email)
    return {"sent": False, "provider": "log", "note": "No RESEND_API_KEY or SMTP configured"}
