import base64
import os

import requests


def build_raw_github_url(repo, branch, file_path):
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"


def upload_certificate_to_github(local_file_path, github_file_path):
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    branch = os.getenv("GITHUB_BRANCH", "main")

    if not token or not repo:
        return None

    api_url = f"https://api.github.com/repos/{repo}/contents/{github_file_path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    with open(local_file_path, "rb") as file_handle:
        content_encoded = base64.b64encode(file_handle.read()).decode("utf-8")

    payload = {
        "message": f"Upload certificate {os.path.basename(github_file_path)}",
        "content": content_encoded,
        "branch": branch,
    }

    # If file already exists, include SHA to update instead of creating duplicate.
    existing = requests.get(api_url, headers=headers, timeout=20)
    if existing.status_code == 200:
        payload["sha"] = existing.json().get("sha")

    response = requests.put(api_url, headers=headers, json=payload, timeout=20)
    if response.status_code not in (200, 201):
        return None

    return build_raw_github_url(repo, branch, github_file_path)
