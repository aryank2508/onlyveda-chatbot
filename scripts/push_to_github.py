import urllib.request
import json
import subprocess
import os

TOKEN = os.environ.get("GH_TOKEN", "")
REPO_NAME = "onlyveda-chatbot"
USERNAME = "aryank2508"


# 1. Create GitHub Repository via API
print(f"Creating repository '{REPO_NAME}' on GitHub under user '{USERNAME}'...")

create_repo_url = "https://api.github.com/user/repos"
payload = {
    "name": REPO_NAME,
    "description": "OnlyVeda Multilingual AI Health Chatbot with 129 Products & 78 Disease Protocols",
    "private": False,
    "has_issues": True,
    "has_wiki": False
}

req = urllib.request.Request(
    create_repo_url,
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "OnlyVeda-Deployment"
    }
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print(f"Repository created successfully: {res.get('html_url')}")
except urllib.error.HTTPError as e:
    if e.code == 422:
        print("Repository already exists on GitHub. Proceeding to push...")
    else:
        print(f"HTTP Error creating repo: {e.code} - {e.read().decode()}")

# 2. Configure Git and push
authenticated_url = f"https://{USERNAME}:{TOKEN}@github.com/{USERNAME}/{REPO_NAME}.git"
public_url = f"https://github.com/{USERNAME}/{REPO_NAME}.git"

print("\nSetting git remote and pushing code...")

# Ensure branch is main
subprocess.run(["git", "branch", "-M", "main"], check=True)

# Set remote
subprocess.run(["git", "remote", "remove", "origin"], stderr=subprocess.DEVNULL)
subprocess.run(["git", "remote", "add", "origin", authenticated_url], check=True)

# Push
push_res = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
print("Git push stdout:", push_res.stdout)
print("Git push stderr:", push_res.stderr)

# Clean up remote URL to remove token for security
subprocess.run(["git", "remote", "set-url", "origin", public_url], check=True)

if push_res.returncode == 0:
    print("\n========================================================")
    print(" ✅ CODE SUCCESSFULLY PUSHED TO GITHUB!")
    print(f" 🔗 Repository URL: {public_url}")
    print("========================================================")
else:
    print(f"Push failed with code {push_res.returncode}")
