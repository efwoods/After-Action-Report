import requests
import datetime
from dateutil import parser
import os
import csv
from dotenv import load_dotenv
import tqdm

load_dotenv()

# === CONFIGURATION ===
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")  # ← Change to your GitHub username
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Optional: GitHub PAT (Personal Access Token)
DAYS_BACK = 7
CSV_OUTPUT = "github_commit_history.csv"

# === Headers for API ===
headers = {
    "Accept": "application/vnd.github+json",
}
if GITHUB_TOKEN:
    headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# === Time Window ===
since_date = (
    datetime.datetime.utcnow() - datetime.timedelta(days=DAYS_BACK)
).isoformat() + "Z"


# === STEP 1: Get All Repos for User ===
def get_all_repos(username):
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}&type=owner"
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(f"GitHub API error: {r.status_code} {r.text}")
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


# === STEP 2: Get Commits from Each Repo ===
def get_commits(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits"
    params = {
        "author": GITHUB_USERNAME,
        "since": since_date,
    }
    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        print(f"No commits for {repo_name}: {r.status_code} {r.text}")
        return []
    return r.json()


# === STEP 3: Aggregate & Sort Chronologically ===
def get_all_recent_commits():
    repos = get_all_repos(GITHUB_USERNAME)
    all_commits = []

    for repo in tqdm(repos, desc="Searching Repos...", ascii=""):
        repo_name = repo["name"]
        commits = get_commits(repo_name)
        for commit in tqdm(commits, desc="Searching Commmits", ascii=""):
            c = commit["commit"]
            date = c["author"]["date"]
            all_commits.append(
                {
                    "repo": repo_name,
                    "date": date,
                    "message": c["message"].strip(),
                    "url": commit["html_url"],
                }
            )

    # Sort by ISO timestamp ascending
    all_commits.sort(key=lambda x: parser.parse(x["date"]))
    return all_commits


# === STEP 4: Save to CSV ===
def save_to_csv(commits):
    with open(CSV_OUTPUT, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "repo", "message", "url"])
        writer.writeheader()
        for c in commits:
            writer.writerow(c)
    print(f"✅ Saved to {CSV_OUTPUT} ({len(commits)} commits)")


# === MAIN ===
if __name__ == "__main__":
    commits = get_all_recent_commits()
    save_to_csv(commits)
    for c in commits:
        print(f"[{c['date']}] {c['repo']} → {c['message']}\n ↳ {c['url']}")
