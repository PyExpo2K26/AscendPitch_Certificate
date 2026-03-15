import os
import logging
from urllib.parse import quote
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for, Response, send_file
from werkzeug.utils import secure_filename

from email_sender import send_certificate_email
from generator import generate_certificate, sanitize_name_for_file
from github_upload import upload_certificate_to_github

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

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
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if is_missing_or_placeholder(github_token):
        logger.warning("GitHub upload disabled: GITHUB_TOKEN is missing or still using a placeholder value")

    if is_missing_or_placeholder(gmail_user) or is_missing_or_placeholder(gmail_password):
        logger.warning("Email delivery disabled: Gmail credentials are missing or still using placeholder values")

    clean_name = sanitize_name_for_file(participant_name)
    certificate_id = clean_name
    certificate_filename = f"{clean_name}.pdf"
    certificate_local_path = os.path.join(CERTIFICATES_DIR, certificate_filename)
    local_certificate_url = url_for("view_certificate", cert_id=certificate_id, _external=True)

    github_file_path = f"{github_folder.strip('/')}/{certificate_filename}".lstrip("/")
    hosted_certificate_url = (
        f"https://pyexpo2k26.github.io/AscendPitch_Certificate/generated-certificates/{certificate_filename}"
    )
    upload_enabled = has_config_value(github_repo) and has_config_value(github_token)
    email_enabled = has_config_value(gmail_user) and has_config_value(gmail_password)
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
            output_path=certificate_local_path,
            participant_name=participant_name,
            college_name=college_name,
            participant_photo_path=photo_path,
            qr_data=verification_link,
            font_path=FONT_PATH,
        )
        logger.info(f"Certificate generated at: {certificate_local_path}")
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

    email_status = "skipped"
    if email_enabled:
        try:
            logger.info(f"Sending certificate email to: {email}")
            send_certificate_email(
                recipient_email=email,
                participant_name=participant_name,
                certificate_path=certificate_local_path,
                certificate_link=certificate_link,
            )
            email_status = "sent"
            logger.info(f"Email sent successfully to: {email}")
        except Exception as e:
            email_status = "failed"
            logger.error(f"Email sending failed: {e}", exc_info=True)
    else:
        flash("Email skipped because GMAIL_USER or GMAIL_APP_PASSWORD is missing or still set to a placeholder value in .env.", "error")
        logger.info("Skipping email delivery because Gmail configuration is incomplete")

    return redirect(
        url_for(
            "success_page",
            name=participant_name,
            email=email,
            cert_id=certificate_id,
            github_url=certificate_link,
            upload_status=upload_status,
            email_status=email_status,
        )
    )


@app.route("/success", methods=["GET"])
def success_page():
    participant_name = request.args.get("name", "")
    recipient_email = request.args.get("email", "")
    certificate_link = request.args.get("github_url", "")
    email_subject = quote("Your Ascend Pitch Certificate")
    email_body = quote(
        f"Hello {participant_name},\n\n"
        f"Download your certificate here:\n{certificate_link}\n\n"
        "Best regards,\nAscend Pitch"
    )
    mailto_link = ""
    if recipient_email and certificate_link:
        mailto_link = f"mailto:{recipient_email}?subject={email_subject}&body={email_body}"

    return render_template(
        "success.html",
        name=participant_name,
        email=recipient_email,
        cert_id=request.args.get("cert_id", ""),
        github_url=certificate_link,
        mailto_link=mailto_link,
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
