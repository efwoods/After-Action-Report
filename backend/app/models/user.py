from sqlalchemy import Column, Integer, String, JSON
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    notion_token = Column(String, nullable=True)
    github_token = Column(String, nullable=True)
    clockify_token = Column(String, nullable=True)