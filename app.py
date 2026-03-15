import os
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from email_sender import send_certificate_email
from generator import generate_certificate, ensure_default_template, sanitize_name_for_file
from github_upload import build_raw_github_url, upload_certificate_to_github

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

CERTIFICATES_DIR = os.path.join(BASE_DIR, "certificates")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATE_IMAGE = os.path.join(STATIC_DIR, "certificate_template.png")
FONT_PATH = os.path.join(STATIC_DIR, "fonts", "DejaVuSans-Bold.ttf")

EVENT_NAME = "Ascend Pitch Certificate Program"
EVENT_DATE = "March 15, 2026"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-this-secret")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def form_page():
    return render_template("form.html", event_name=EVENT_NAME, event_date=EVENT_DATE)


@app.route("/generate", methods=["POST"])
def generate_route():
    participant_name = request.form.get("name", "").strip()
    college_name = request.form.get("college", "").strip()
    email = request.form.get("email", "").strip()
    photo = request.files.get("photo")

    if not all([participant_name, college_name, email, photo]):
        flash("All fields are required.", "error")
        return redirect(url_for("form_page"))

    if not allowed_file(photo.filename):
        flash("Invalid photo format. Allowed: png, jpg, jpeg, webp.", "error")
        return redirect(url_for("form_page"))

    github_repo = os.getenv("GITHUB_REPO")
    github_branch = os.getenv("GITHUB_BRANCH", "main")
    github_folder = os.getenv("GITHUB_CERT_FOLDER", "")
    if not github_repo:
        flash("Set GITHUB_REPO in .env before generating certificates.", "error")
        return redirect(url_for("form_page"))

    clean_name = sanitize_name_for_file(participant_name)
    certificate_filename = f"{clean_name}.png"
    certificate_local_path = os.path.join(CERTIFICATES_DIR, certificate_filename)

    github_file_path = f"{github_folder.strip('/')}/{certificate_filename}".lstrip("/")
    github_raw_url = build_raw_github_url(github_repo, github_branch, github_file_path)

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(CERTIFICATES_DIR, exist_ok=True)

    photo_filename = f"{uuid4().hex}_{secure_filename(photo.filename)}"
    photo_path = os.path.join(UPLOADS_DIR, photo_filename)
    photo.save(photo_path)

    try:
        generate_certificate(
            template_path=TEMPLATE_IMAGE,
            output_path=certificate_local_path,
            participant_name=participant_name,
            college_name=college_name,
            participant_photo_path=photo_path,
            qr_data=github_raw_url,
            font_path=FONT_PATH,
        )
    except Exception as exc:
        flash(f"Certificate generation failed: {exc}", "error")
        return redirect(url_for("form_page"))

    uploaded_url = upload_certificate_to_github(
        local_file_path=certificate_local_path,
        github_file_path=github_file_path,
    )
    if not uploaded_url:
        flash("GitHub upload failed. Check token/repository settings.", "error")
        return redirect(url_for("form_page"))

    email_status = "sent"
    try:
        send_certificate_email(
            recipient_email=email,
            participant_name=participant_name,
            certificate_path=certificate_local_path,
            certificate_link=uploaded_url,
        )
    except Exception:
        email_status = "failed"

    return redirect(
        url_for(
            "success_page",
            name=participant_name,
            email=email,
            github_url=uploaded_url,
            email_status=email_status,
        )
    )


@app.route("/success", methods=["GET"])
def success_page():
    return render_template(
        "success.html",
        name=request.args.get("name", ""),
        email=request.args.get("email", ""),
        github_url=request.args.get("github_url", ""),
        email_status=request.args.get("email_status", "unknown"),
    )


if __name__ == "__main__":
    os.makedirs(CERTIFICATES_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)
    ensure_default_template(TEMPLATE_IMAGE)
    app.run(debug=True)
