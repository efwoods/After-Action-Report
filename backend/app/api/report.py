from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.api.integrations import notion, github, clockify
from app.core.llm import generate_report
import redis
from app.core.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
redis_client = redis.Redis.from_url(settings.REDIS_URL)

@router.get("/generate")
def generate_weekly_report(email: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check cache
    cache_key = f"report:{email}"
    cached_report = redis_client.get(cache_key)
    if cached_report:
        return {"report": cached_report.decode("utf-8")}
    
    # Fetch data
    data = {}
    if db_user.notion_token:
        data["notion"] = notion.get_notion_data(db_user.notion_token)
    if db_user.github_token:
        data["github"] = github.get_github_data(db_user.github_token)
    if db_user.clockify_token:
        data["clockify"] = clockify.get_clockify_data(db_user.clockify_token)
    
    # Generate report
    report = generate_report(data)
    
    # Cache report (expire after 1 hour)
    redis_client.setex(cache_key, 3600, report)
    
    return {"report": report}