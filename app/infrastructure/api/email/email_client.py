import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.infrastructure.config.config import settings

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 2.0


def send_email(to: str, subject: str, body_html: str, body_text: str) -> None:
    last_error: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            _send_via_smtp(to, subject, body_html, body_text)
            logger.info("Email sent successfully to=%s subject=%s", to, subject)
            return
        except Exception as e:
            last_error = e
            logger.warning(
                "Email send attempt %d/%d failed to=%s error=%s",
                attempt, _MAX_RETRIES, to, e,
            )
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY_SECONDS * attempt)

    logger.error("All email send attempts failed to=%s error=%s", to, last_error)
    raise RuntimeError(f"Failed to send email after {_MAX_RETRIES} attempts: {last_error}") from last_error


def _send_via_smtp(to: str, subject: str, body_html: str, body_text: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM or settings.SMTP_USER
    msg["To"] = to
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(msg["From"], [to], msg.as_string())
