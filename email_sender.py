import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_certificate_email(
    recipient_email,
    participant_name,
    certificate_path,
    certificate_link,
):
    sender_email = os.getenv("GMAIL_USER")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender_email or not app_password:
        raise RuntimeError("Missing GMAIL_USER or GMAIL_APP_PASSWORD environment variables")

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
        attachment = MIMEApplication(file_handle.read(), _subtype="png")
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=os.path.basename(certificate_path),
        )
        message.attach(attachment)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(sender_email, app_password)
        smtp.sendmail(sender_email, recipient_email, message.as_string())
