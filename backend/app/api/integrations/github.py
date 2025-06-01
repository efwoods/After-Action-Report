import requests
from datetime import datetime, timedelta

def get_github_data(token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    start_date = (datetime.now() - timedelta(days=7)).isoformat()
    data = {
        "commits": [],
        "issues": [],
        "prs": [],
    }
    # Get user repositories
    repos = requests.get("https://api.github.com/user/repos", headers=headers).json()
    for repo in repos:
        # Commits
        commits = requests.get(
            f"https://api.github.com/repos/{repo['full_name']}/commits",
            headers=headers,
            params={"since": start_date}
        ).json()
        data["commits"].extend(commits)
        # Issues
        issues = requests.get(
            f"https://api.github.com/repos/{repo['full_name']}/issues",
            headers=headers,
            params={"since": start_date}
        ).json()
        data["issues"].extend(issues)
        # PRs
        prs = requests.get(
            f"https://api.github.com/repos/{repo['full_name']}/pulls",
            headers=headers,
            params={"state": "all"}
        ).json()
        data["prs"].extend([pr for pr in prs if pr["created_at"] >= start_date or pr["updated_at"] >= start_date])
    return data