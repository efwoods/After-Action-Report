import requests
from datetime import datetime, timedelta
from app.core.config import settings

def get_notion_data(token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    # Assume database IDs are known or retrieved dynamically
    database_ids = ["project_ideas_db_id", "subproject1_db_id", "subproject2_db_id", "subproject3_db_id"]
    data = {}
    start_date = (datetime.now() - timedelta(days=7)).isoformat()
    for db_id in database_ids:
        response = requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            headers=headers,
            json={"filter": {"timestamp": "last_edited_time", "last_edited_time": {"after": start_date}}}
        )
        data[db_id] = response.json().get("results", [])
    return data