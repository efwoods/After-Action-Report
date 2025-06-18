import requests
from app.core.config import settings

def generate_report(data: dict) -> str:
    prompt = f"""
    Analyze the following data for the past week:
    Notion: {data['notion']}
    GitHub: {data['github']}
    Clockify: {data['clockify']}
    
    Provide a report addressing:
    1. How the user spent their time.
    2. What worked and improved.
    3. What didn't work.
    4. New standards for excellence.
    """
    response = requests.post(
        f"{settings.OLLAMA_HOST}/api/generate",
        json={"model": "llama3", "prompt": prompt, "stream": False}
    )
    return response.json().get("response", "Error generating report")