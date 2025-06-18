import requests
from datetime import datetime, timedelta
from app.core.config import settings

def get_clockify_data(token: str) -> dict:
    headers = {"X-Api-Key": token}
    user = requests.get("https://api.clockify.me/api/v1/user", headers=headers).json()
    workspace_id = user["defaultWorkspace"]
    start_date = (datetime.now() - timedelta(days=7)).isoformat()
    end_date = datetime.now().isoformat()
    time_entries = requests.get(
        f"https://api.clockify.me/api/v1/workspaces/{workspace_id}/user/{user['id']}/time-entries",
        headers=headers,
        params={"start": start_date, "end": end_date}
    ).json()
    return {"time_entries": time_entries}