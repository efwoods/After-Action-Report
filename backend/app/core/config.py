import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@postgres:5432/aar"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "your-secret-key"  # Replace with secure key
    NOTION_CLIENT_ID: str = "your-notion-client-id"
    NOTION_CLIENT_SECRET: str = "your-notion-client-secret"
    GITHUB_CLIENT_ID: str = "your-github-client-id"
    GITHUB_CLIENT_SECRET: str = "your-github-client-secret"
    CLOCKIFY_API_KEY: str = "your-clockify-api-key"
    OLLAMA_HOST: str = "http://localhost:11434"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()