import base64
import os

import requests


def build_raw_github_url(repo, branch, file_path):
    """Build the raw GitHub URL for accessing a file from the repository."""
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"


def upload_certificate_to_github(local_file_path, github_file_path):
    """
    Upload a certificate file to GitHub using the GitHub REST API.
    
    Args:
        local_file_path: Path to the local certificate file
        github_file_path: Destination path in GitHub repository
    
    Returns:
        The raw GitHub URL of the uploaded file, or None if upload failed
    """
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    branch = os.getenv("GITHUB_BRANCH", "main")

    if not token or not repo:
        print("[ERROR] GitHub upload failed: Missing GITHUB_TOKEN or GITHUB_REPO environment variables")
        return None

    api_url = f"https://api.github.com/repos/{repo}/contents/{github_file_path}"
    # Use 'token' format for Personal Access Token authentication (not 'Bearer')
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        with open(local_file_path, "rb") as file_handle:
            content_encoded = base64.b64encode(file_handle.read()).decode("utf-8")

        payload = {
            "message": f"Upload certificate {os.path.basename(github_file_path)}",
            "content": content_encoded,
            "branch": branch,
        }

        # Check if file already exists to avoid duplicate uploads
        print(f"[INFO] Checking if file exists at {api_url}")
        existing = requests.get(api_url, headers=headers, timeout=20)
        
        if existing.status_code == 200:
            print("[INFO] File exists, will update it")
            payload["sha"] = existing.json().get("sha")
        elif existing.status_code == 404:
            print("[INFO] File does not exist, will create it")
        else:
            print(f"[WARNING] Unexpected response checking file existence: {existing.status_code}")

        # Upload or update the certificate
        print(f"[INFO] Uploading certificate to GitHub...")
        response = requests.put(api_url, headers=headers, json=payload, timeout=20)
        
        if response.status_code in (200, 201):
            print(f"[SUCCESS] Certificate uploaded successfully. Status: {response.status_code}")
            return build_raw_github_url(repo, branch, github_file_path)
        else:
            print(f"[ERROR] GitHub API error: {response.status_code}")
            print(f"[ERROR] Response: {response.text}")
            try:
                error_data = response.json()
                print(f"[ERROR] GitHub response JSON: {error_data}")
            except ValueError:
                pass
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error during GitHub upload: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error during GitHub upload: {e}")
        return None
