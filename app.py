import os
import logging
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for, Response, send_file
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

from generator import generate_certificate, sanitize_name_for_file
from github_upload import upload_certificate_to_github

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
dotenv_loaded = load_dotenv(dotenv_path=ENV_PATH)
logger.info(f"Dotenv loaded from {ENV_PATH}: {dotenv_loaded}")
COUNTER_FILE = os.path.join(BASE_DIR, "certificate_counter.txt")

CERTIFICATES_DIR = os.path.join(BASE_DIR, "certificates")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_IMAGE = os.path.join(STATIC_DIR, "certificate_template.png")
FONT_PATH = os.path.join(STATIC_DIR, "fonts", "DejaVuSans-Bold.ttf")

EVENT_NAME = "Ascend Pitch"
EVENT_DATE = "March 28, 2026"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-this-secret")
mail_username = os.getenv("MAIL_USERNAME")
mail_password = os.getenv("MAIL_PASSWORD")
logger.info(f"MAIL_USERNAME loaded: {bool(mail_username)}")
logger.info(f"MAIL_PASSWORD loaded: {bool(mail_password)}")
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = mail_username
app.config["MAIL_PASSWORD"] = mail_password
app.config["MAIL_DEFAULT_SENDER"] = mail_username


def validate_mail_configuration():
    missing = []
    if not app.config.get("MAIL_USERNAME"):
        missing.append("MAIL_USERNAME")
    if not app.config.get("MAIL_PASSWORD"):
        missing.append("MAIL_PASSWORD")

    if missing:
        raise RuntimeError(
            f"Missing required mail configuration: {', '.join(missing)}. "
            "Set these values in the project root .env file."
        )


validate_mail_configuration()

mail = Mail(app)


def send_certificate_email(
    to_email,
    name,
    verification_link,
    certificate_path,
    attachment_filename,
):
    """Send certificate email with verification link and PDF attachment."""
    validate_mail_configuration()
    msg = Message(
        subject="Certificate Generated",
        recipients=[to_email],
        body=(
            f"Dear {name},\n\n"
            "Thank you for participating in the AscendPitch held at KGiSL Institute of Technology on 28.03.2026.\n"
            "We hope you gained a better experience at the event.\n\n"
            "Your certificate is attached in this mail.\n\n"
            "Verification link:\n"
            f"{verification_link}\n\n"
            "Thank you\n\n"
            "Best Regards,\n"
            "PyExpo Crew"
        ),
    )
    with open(certificate_path, "rb") as certificate_file:
        file_data = certificate_file.read()

    msg.attach(attachment_filename, "application/pdf", file_data)
    mail.send(msg)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def has_config_value(value):
    if not value:
        return False
    lowered = value.strip().lower()
    placeholder_fragments = ("your_", "your-", "change-this", "example", "placeholder")
    return not any(fragment in lowered for fragment in placeholder_fragments)


def is_missing_or_placeholder(value):
    return not has_config_value(value)


def generate_certificate_id():
    """Generate a unique sequential certificate ID like ASCEND-2026-0001."""
    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "w", encoding="utf-8") as counter_file:
            counter_file.write("1")

    try:
        with open(COUNTER_FILE, "r", encoding="utf-8") as counter_file:
            raw_value = counter_file.read().strip()
            counter = int(raw_value) if raw_value else 1
    except (OSError, ValueError):
        counter = 1

    certificate_id = f"ASCEND-2026-{counter:04d}"

    with open(COUNTER_FILE, "w", encoding="utf-8") as counter_file:
        counter_file.write(str(counter + 1))

    return certificate_id


@app.route("/", methods=["GET"])
def form_page():
    return render_template("form.html", event_name=EVENT_NAME, event_date=EVENT_DATE)


@app.route("/certificate/<cert_id>")
def view_certificate(cert_id):
    """Serve certificate PDF inline (display in browser, not download)."""
    certificate_path = os.path.join(CERTIFICATES_DIR, f"{cert_id}.pdf")
    
    logger.info(f"Attempting to serve certificate: {certificate_path}")
    
    if not os.path.exists(certificate_path):
        logger.warning(f"Certificate not found: {certificate_path}")
        return "Certificate not found", 404
    
    logger.info(f"Serving certificate: {certificate_path}")
    
    try:
        with open(certificate_path, 'rb') as f:
            pdf_data = f.read()
        
        response = Response(pdf_data, mimetype='application/pdf')
        response.headers['Content-Disposition'] = 'inline; filename=certificate.pdf'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"Error serving certificate: {e}")
        return f"Error serving certificate: {e}", 500


@app.route("/certificate/<cert_id>/download")
def download_certificate(cert_id):
    certificate_path = os.path.join(CERTIFICATES_DIR, f"{cert_id}.pdf")

    if not os.path.exists(certificate_path):
        logger.warning(f"Certificate not found for download: {certificate_path}")
        return "Certificate not found", 404

    return send_file(
        certificate_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{cert_id}.pdf",
    )


@app.route("/generate", methods=["POST"])
def generate_route():
    participant_name = request.form.get("name", "").strip()
    college_name = request.form.get("college", "").strip()
    email = request.form.get("email", "").strip()
    photo = request.files.get("photo")

    logger.info(f"Certificate generation request for: {participant_name}")

    if not all([participant_name, college_name, email, photo]):
        flash("All fields are required.", "error")
        logger.warning("Missing required fields in certificate request")
        return redirect(url_for("form_page"))

    if not photo.filename or not allowed_file(photo.filename):
        flash("Upload a valid photo. Allowed: png, jpg, jpeg, webp.", "error")
        logger.warning("Missing or invalid participant photo")
        return redirect(url_for("form_page"))

    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")
    github_branch = os.getenv("GITHUB_BRANCH", "main")
    github_folder = os.getenv("GITHUB_CERT_FOLDER", "generated-certificates")
    if is_missing_or_placeholder(github_token):
        logger.warning("GitHub upload disabled: GITHUB_TOKEN is missing or still using a placeholder value")

    clean_name = sanitize_name_for_file(participant_name)
    college_first_word = college_name.strip().split()[0] if college_name.strip() else "college"
    clean_college = sanitize_name_for_file(college_first_word)
    certificate_id = generate_certificate_id()
    certificate_stem = f"{clean_name}_{clean_college}_{certificate_id}"
    certificate_filename = f"{certificate_stem}.pdf"
    certificate_local_path = os.path.join(CERTIFICATES_DIR, certificate_filename)
    output_path = certificate_local_path
    local_certificate_url = url_for("view_certificate", cert_id=certificate_stem, _external=True)

    github_file_path = f"{github_folder.strip('/')}/{certificate_filename}".lstrip("/")
    hosted_certificate_url = (
        f"https://pyexpo2k26.github.io/AscendPitch_Certificate/generated-certificates/{certificate_filename}"
    )
    upload_enabled = has_config_value(github_repo) and has_config_value(github_token)
    verification_link = hosted_certificate_url if upload_enabled else local_certificate_url

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(CERTIFICATES_DIR, exist_ok=True)

    photo_filename = f"{uuid4().hex}_{secure_filename(photo.filename)}"
    photo_path = os.path.join(UPLOADS_DIR, photo_filename)
    photo.save(photo_path)
    logger.info(f"Photo saved to: {photo_path}")

    try:
        logger.info("Generating certificate...")
        generate_certificate(
            template_path=TEMPLATE_IMAGE,
            output_path=output_path,
            participant_name=participant_name,
            college_name=college_name,
            participant_photo_path=photo_path,
            qr_data=verification_link,
            font_path=FONT_PATH,
        )
        logger.info(f"Certificate generated at: {output_path}")
    except Exception as exc:
        flash(f"Certificate generation failed: {exc}", "error")
        logger.error(f"Certificate generation error: {exc}", exc_info=True)
        return redirect(url_for("form_page"))
    finally:
        try:
            if os.path.exists(photo_path):
                os.remove(photo_path)
        except OSError as exc:
            logger.warning(f"Could not remove temporary photo {photo_path}: {exc}")

    upload_status = "skipped"
    certificate_link = local_certificate_url
    if upload_enabled:
        logger.info(f"Uploading to GitHub repo: {github_repo}, path: {github_file_path}")
        uploaded_url = upload_certificate_to_github(
            local_file_path=certificate_local_path,
            github_file_path=github_file_path,
            cleanup_local=False,
        )
        if uploaded_url:
            upload_status = "uploaded"
            certificate_link = hosted_certificate_url
            logger.info(f"Certificate successfully uploaded to: {uploaded_url}")
        else:
            upload_status = "failed"
            logger.error(f"GitHub upload failed for {participant_name}; using local certificate link")
            flash("Certificate generated locally, but GitHub upload failed.", "error")
    else:
        flash("GitHub upload skipped because GITHUB_TOKEN is missing or still set to the placeholder value in .env.", "error")

    email_status = "failed"
    try:
        logger.info(f"Sending certificate email to: {email}")
        send_certificate_email(
            email,
            participant_name,
            certificate_link,
            output_path,
            certificate_filename,
        )
        email_status = "sent"
        logger.info(f"Email sent successfully to: {email}")
    except Exception as e:
        logger.error(f"Email sending failed: {e}", exc_info=True)
        flash(f"Email sending failed: {e}", "error")

    return redirect(
        url_for(
            "success_page",
            name=participant_name,
            email=email,
            cert_id=certificate_stem,
            github_url=certificate_link,
            upload_status=upload_status,
            email_status=email_status,
        )
    )


@app.route("/success", methods=["GET"])
def success_page():
    return render_template(
        "success.html",
        name=request.args.get("name", ""),
        email=request.args.get("email", ""),
        cert_id=request.args.get("cert_id", ""),
        github_url=request.args.get("github_url", ""),
        upload_status=request.args.get("upload_status", "skipped"),
        email_status=request.args.get("email_status", "unknown"),
    )


if __name__ == "__main__":
    logger.info("Starting Flask application...")
    logger.info(f"GitHub Repo: {os.getenv('GITHUB_REPO', 'Not configured')}")
    logger.info(f"GitHub Branch: {os.getenv('GITHUB_BRANCH', 'main')}")
    
    os.makedirs(CERTIFICATES_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
    # ensure_default_template(TEMPLATE_IMAGE)
    app.run(debug=True)
