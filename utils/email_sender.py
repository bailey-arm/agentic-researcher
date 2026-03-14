"""Email utility for sending research outputs."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

DEFAULT_RECIPIENT = "bailey.arm.business@gmail.com"

# Configure via env vars:
#   EMAIL_SENDER   - sender email address
#   EMAIL_PASSWORD - app password (Gmail requires an "App Password")
#   EMAIL_SMTP     - SMTP server (default: smtp.gmail.com)
#   EMAIL_PORT     - SMTP port (default: 587)


def send_research_email(
    subject: str,
    body_markdown: str,
    chart_paths: list[str] | None = None,
    recipient: str | None = None,
) -> str:
    """Send a research output via email.

    Args:
        subject: Email subject line.
        body_markdown: The research output as markdown text.
        chart_paths: Optional list of chart image file paths to attach.
        recipient: Recipient email. Defaults to EMAIL_RECIPIENT env var
                   or bailey.arm.business@gmail.com.

    Returns:
        Status message string.
    """
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    smtp_server = os.environ.get("EMAIL_SMTP", "smtp.gmail.com")
    smtp_port = int(os.environ.get("EMAIL_PORT", "587"))
    recipient = recipient or os.environ.get("EMAIL_RECIPIENT", DEFAULT_RECIPIENT)

    if not sender or not password:
        return (
            "Email not configured. Set EMAIL_SENDER and EMAIL_PASSWORD "
            "environment variables to enable email delivery."
        )

    msg = MIMEMultipart("mixed")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    # Attach the markdown body as plain text
    msg.attach(MIMEText(body_markdown, "plain", "utf-8"))

    # Attach chart images if any
    for i, path in enumerate(chart_paths or []):
        if os.path.exists(path):
            with open(path, "rb") as f:
                img = MIMEImage(f.read(), name=os.path.basename(path))
                img.add_header(
                    "Content-Disposition", "attachment",
                    filename=os.path.basename(path),
                )
                msg.attach(img)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        return f"Email sent to {recipient}"
    except Exception as e:
        return f"Failed to send email: {e}"
