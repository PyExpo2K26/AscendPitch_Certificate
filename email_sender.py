import os
import smtplib
import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_certificate_email(
    recipient_email,
    participant_name,
    certificate_path,
    certificate_link,
):
    sender_email = (os.getenv("MAIL_USERNAME") or "").strip()
    raw_password = os.getenv("MAIL_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD") or ""
    app_password = raw_password.replace(" ", "")

    if raw_password and raw_password != app_password:
        logger.warning("MAIL_PASSWORD contained spaces; spaces were removed before SMTP login")

    if not sender_email:
        raise RuntimeError("Missing MAIL_USERNAME environment variable")

    if not app_password:
        raise RuntimeError("Missing MAIL_PASSWORD or GMAIL_APP_PASSWORD environment variables")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = "Your Event Certificate"

    body = (
        f"Hello {participant_name},\n\n"
        "Congratulations on participating in our event.\n\n"
        "Download your certificate here:\n"
        f"{certificate_link}\n\n"
        "The certificate is attached to this email.\n\n"
        "Best regards,\nEvent Organizer"
    )
    message.attach(MIMEText(body, "plain"))

    with open(certificate_path, "rb") as file_handle:
        attachment = MIMEApplication(file_handle.read(), _subtype="pdf")
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=os.path.basename(certificate_path),
        )
        message.attach(attachment)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        try:
            smtp.login(sender_email, app_password)
            smtp.sendmail(sender_email, recipient_email, message.as_string())
        except smtplib.SMTPAuthenticationError:
            logger.error(
                "SMTP authentication failed for %s. Use Gmail App Password and ensure MAIL_USERNAME matches sender.",
                sender_email,
                exc_info=True,
            )
            raise
        except smtplib.SMTPException as exc:
            logger.error("SMTP error while sending email to %s: %s", recipient_email, exc, exc_info=True)
            raise
