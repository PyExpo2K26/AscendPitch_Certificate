# Event Certificate Generator System

Flask-based web application that generates participant certificates from a fixed template, uploads certificates to GitHub, embeds GitHub raw URL QR codes, and emails certificates to participants.

## Features

- Fixed template: `static/certificate_template.png`
- Dynamic fields: participant name, college name, participant photo, QR code
- File naming: `certificates/Participant_Name.png`
- GitHub upload through REST API
- QR code contains GitHub raw certificate URL
- Email delivery using Gmail SMTP app password

## Project Structure

```text
project/
  app.py
  generator.py
  github_upload.py
  email_sender.py

  certificates/

  static/
    certificate_template.png
    fonts/

  templates/
    form.html
    success.html
```

## Environment Variables

Create a `.env` file in the project root:

```env
FLASK_SECRET_KEY=replace-with-strong-secret

GMAIL_USER=yourgmail@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password

GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=username/event-certificates
GITHUB_BRANCH=main
GITHUB_CERT_FOLDER=
```

Notes:
- `GITHUB_REPO` should be in the format `username/repo`.
- Leave `GITHUB_CERT_FOLDER` empty to upload files in repository root.
- Set `GITHUB_CERT_FOLDER=certificates` to upload into a subfolder.

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the App

```bash
python app.py
```

Open in browser:

- http://127.0.0.1:5000/

## Certificate Flow

1. Fill participant name, college, email, and upload photo.
2. App builds a file name from participant name (for example: `John_Doe.png`).
3. App builds GitHub raw URL using repo/branch/path.
4. QR code is generated with this GitHub raw URL and placed in the bottom-right corner.
5. Certificate is saved in `certificates/`.
6. Certificate is uploaded to GitHub.
7. Certificate is emailed to participant with attachment and link.
