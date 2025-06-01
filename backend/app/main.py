from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, report
from app.core.database import engine
from app.models import user
import uvicorn

app = FastAPI(title="After Action Report API")

# CORS setup for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-vercel-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/auth")
app.include_router(report.router, prefix="/report")

# Create database tables
user.Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)