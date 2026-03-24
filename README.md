# Event Certificate Generator System

Flask-based web application that generates participant certificates from a fixed template, uploads certificates to GitHub, embeds GitHub raw URL QR codes, and emails certificates to participants.

## Features

- Fixed template-based certificate generation: `static/certificate_template.jpeg`
- Dynamic fields: participant name, college name, participant photo
- Automatic file naming: `certificates/Participant_Name.png`
- GitHub REST API integration for certificate uploads
- QR code generation containing GitHub raw certificate URL
- Email delivery using Gmail SMTP with a fixed sender address
- Proper error handling and logging for debugging
- Environment-based configuration with `.env` file

## Project Structure

```
project/
├── app.py                          # Flask application
├── render.yaml                     # Render deployment config
├── generator.py                    # Certificate generation logic
├── github_upload.py                # GitHub API integration
├── email_sender.py                 # Email functionality
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (DO NOT COMMIT)
├── .env.example                    # Example environment variables
├── .gitignore                      # Git ignore rules
│
├── certificates/                   # Generated certificates
├── uploads/                        # Temporary photo uploads
├── generated-certificates/         # (Optional) GitHub upload destination
│
├── static/
│   ├── certificate_template.jpeg   # Default certificate template
│   └── fonts/
│       └── DejaVuSans-Bold.ttf     # Required font file
│
└── templates/
    ├── form.html                   # Certificate generation form
    └── success.html                # Success page
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Flask Configuration
FLASK_SECRET_KEY=your-very-secure-random-string

# GitHub Configuration
GITHUB_TOKEN=ghp_your_personal_access_token_here
GITHUB_REPO=your-organization/event-certificates
GITHUB_BRANCH=main
GITHUB_CERT_FOLDER=certificates

# Email Configuration
# The app always sends from: pyexpo@kgkite.ac.in

# Generate app password from: https://myaccount.google.com/apppasswords
# This is NOT your regular Gmail password
MAIL_PASSWORD=your-gmail-app-password

# Optional legacy alias used by email_sender.py
GMAIL_APP_PASSWORD=your-gmail-app-password
```

### 3. GitHub Personal Access Token Setup

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Set scopes:
   - ✓ `repo` (Full control of private repositories)
4. Copy the token (starts with `ghp_`)
5. Add to `.env` as `GITHUB_TOKEN`

### 4. GitHub Repository Setup

- Create a repository with the name specified in `GITHUB_REPO`
- The repository can be public or private
- The branch (default `main`) must exist
- Optional: Create a `certificates/` folder if using `GITHUB_CERT_FOLDER`

### 5. (Optional) Gmail Setup for Email Delivery

1. Enable 2-factor authentication on your Gmail account
2. Go to https://myaccount.google.com/apppasswords
3. Select Mail and Windows Computer
4. Generate an app password
5. Use this password (16 characters) as `MAIL_PASSWORD` in Render or `.env`

### 6. Deploy on Render

1. Push the repository to GitHub.
2. In Render, create a new Web Service from the repository.
3. Render should detect [render.yaml](render.yaml) automatically, or you can use it as the blueprint.
4. Add these environment variables in the Render dashboard if they are not already synced:
   - `FLASK_SECRET_KEY`
   - `MAIL_PASSWORD`
   - `GITHUB_TOKEN`
   - `GITHUB_REPO`
   - `GITHUB_BRANCH`
   - `GITHUB_CERT_FOLDER`
   - `APP_STORAGE_DIR`
5. Deploy the project.

Notes for Render:
- The sender address is fixed in code as `pyexpo@kgkite.ac.in`.
- Runtime certificate and upload files are written to the Render disk mounted at `/var/data/ascendpitch`.
- Keep GitHub upload enabled so the verification link remains accessible after the request finishes.

## Running the Application

```bash
python app.py
```

The application will start on:
- **Local**: http://127.0.0.1:5000/
- **Network**: http://<your-ip>:5000/

## Certificate Generation Flow

1. User fills out the form:
   - Participant Name
   - College Name
   - Email Address
   - Photo Upload
2. App sanitizes participant name and creates filename (e.g., `John_Doe.png`)
3. QR code URL is generated: `https://raw.githubusercontent.com/{repo}/{branch}/{file_path}`
4. Certificate image is generated with:
   - Participant name (centered)
   - College name (centered)
   - Participant photo (bottom-left corner)
   - QR code (bottom-right corner)
5. Certificate is saved locally to `certificates/`
6. Certificate is uploaded to GitHub via REST API
7. Certificate email is sent to participant (if configured)

## Troubleshooting

### "GitHub upload failed. Check token/repository settings."

**Check the console output** for detailed error messages. Common issues:

1. **Invalid Token**: 
   - Token may be expired or revoked
   - Generate a new token from https://github.com/settings/tokens

2. **Wrong Repository Name**:
   - Format must be: `organization/repository`
   - Check spelling and case sensitivity
   - Repository must exist

3. **Missing Permissions**:
   - Token must have `repo` scope
   - Token must have write access to the repository

4. **Network Issues**:
   - Check internet connection
   - Verify no firewall blocks api.github.com

### Certificate Generation Fails

- Ensure `static/certificate_template.jpeg` exists
- Ensure `static/fonts/DejaVuSans-Bold.ttf` exists (or update path in app.py)
- Check photo format: PNG, JPG, JPEG, or WebP
- Check console logs for specific errors

### Email Not Sending

- Verify `MAIL_PASSWORD` is set correctly
- Ensure Gmail account has 2FA enabled
- Use app-generated password, not regular Gmail password
- Check console logs for SMTP errors

### Render Deployment Issues

- Confirm the project has been deployed with [render.yaml](render.yaml)
- Make sure all required environment variables are set in the Render dashboard
- Do not rely on locally stored certificate files; use GitHub upload for persistent links

## Logging

The application logs important events to console. Look for:
- `[INFO]` - Normal operations
- `[WARNING]` - Potential issues
- `[ERROR]` - Critical failures

Run with console visible to diagnose issues.

## Security Notes

- **Never commit `.env`** - It contains sensitive tokens
- **Use strong `FLASK_SECRET_KEY`** - Generate with `python -c "import secrets; print(secrets.token_hex(16))"`
- **GitHub tokens are sensitive** - Treat like passwords
- **Email passwords are sensitive** - Use app-specific passwords, not account passwords
- The `.gitignore` file ignores sensitive files and generated certificates

## Dependencies

See `requirements.txt` for the complete list:
- Flask 3.1.0 - Web framework
- Pillow 11.1.0 - Image processing
- qrcode 8.0 - QR code generation
- requests 2.32.3 - HTTP library for GitHub API
- python-dotenv 1.0.1 - Environment variable loading
