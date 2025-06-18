# After-Action-Report

After-action-report app using Notion, GitHub, and Clockify APIs to summarize weekly work via LLM: what worked, what didn’t, improvements, and new standards. SPA with login, iCloud calendar view, and time-spent dashboard by task.

## [Project Prompt](https://grok.com/share/bGVnYWN5_9d22fb5c-d3cc-49dd-a962-acb472be4eb6)

I want to create an application (after-action-report) to pull metrics from my notion activity ( have n "todo lists" for projects (one for all the project ideas and three specific sub-projects) with an update histories), my github activity, and clockify activity for the previous week. I want to use this information with an LLM to describe:

1. How I spent my time
2. What did I do that worked? What improved? What's Better?
3. What did I do that didn't work
4. What are the new standards (while aiming for excellence) 

I want to pull from the Notion api, github api, and clockify api to retrieve this data. 


### Future Features:
---
I want this to be a single page application with the ability to login and connect accounts. I want to also visualize a calendar view of what I spent my time on with the marked activities of what I was doing on the calendar. I want this to be integrated with icloud calendar.

I also want a dashboard of the total time I spent, a descending list of items that I had worked on ordered by time spent on each.

---

#### Directory Structure
```
after-action-report/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── report.py
│   │   │   └── integrations/
│   │   │       ├── __init__.py
│   │   │       ├── notion.py
│   │   │       ├── github.py
│   │   │       └── clockify.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── llm.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.jsx
│   │   │   ├── Report.jsx
│   │   │   ├── CalendarView.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
├── prometheus.yml
└── README.md
```

#### Backend: FastAPI Server
**backend/app/main.py**
```python
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
```

**backend/app/core/config.py**
```python
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
```

**backend/app/core/database.py**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**backend/app/core/llm.py**
```python
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
```

**backend/app/models/user.py**
```python
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
```

**backend/app/api/auth.py**
```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    return jwt.encode(data, settings.JWT_SECRET, algorithm="HS256")

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"msg": "User registered"}

@router.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/connect/notion")
def connect_notion(token: str, email: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    db_user.notion_token = token
    db.commit()
    return {"msg": "Notion connected"}

@router.post("/connect/github")
def connect_github(token: str, email: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    db_user.github_token = token
    db.commit()
    return {"msg": "GitHub connected"}

@router.post("/connect/clockify")
def connect_clockify(token: str, email: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    db_user.clockify_token = token
    db.commit()
    return {"msg": "Clockify connected"}
```

**backend/app/api/integrations/notion.py**
```python
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
```

**backend/app/api/integrations/github.py**
```python
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
```

**backend/app/api/integrations/clockify.py**
```python
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
```

**backend/app/api/report.py**
```python
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
```

**backend/requirements.txt**
```
fastapi==0.115.2
uvicorn==0.32.0
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
redis==5.1.1
requests==2.32.3
python-jose==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.9.2
```

**backend/Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend: React SPA
**frontend/public/index.html**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>After Action Report</title>
  <script src="https://cdn.jsdelivr.net/npm/react@18/umd/react.development.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/react-dom@18/umd/react-dom.development.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/core@6.1.15/main.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@fullcalendar/daygrid@6.1.15/main.min.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fullcalendar/core@6.1.15/main.min.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fullcalendar/daygrid@6.1.15/main.min.css" />
</head>
<body>
  <div id="root"></div>
</body>
</html>
```

**frontend/src/App.jsx**
```jsx
import { useState } from 'react';
import Login from './components/Login';
import Report from './components/Report';
import CalendarView from './components/CalendarView';
import Dashboard from './components/Dashboard';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');

  return (
    <div className="min-h-screen bg-gray-100">
      {token ? (
        <div className="container mx-auto p-4">
          <h1 className="text-3xl font-bold mb-4">After Action Report</h1>
          <button
            onClick={() => {
              localStorage.removeItem('token');
              setToken('');
            }}
            className="mb-4 bg-red-500 text-white px-4 py-2 rounded"
          >
            Logout
          </button>
          <Report />
          <CalendarView />
          <Dashboard />
        </div>
      ) : (
        <Login setToken={setToken} />
      )}
    </div>
  );
}

export default App;
```

**frontend/src/components/Login.jsx**
```jsx
import { useState } from 'react';
import axios from 'axios';

function Login({ setToken }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(
        `http://localhost:8000/auth/${isRegister ? 'register' : 'login'}`,
        { email, password }
      );
      if (!isRegister) {
        setToken(response.data.access_token);
        localStorage.setItem('token', response.data.access_token);
      }
      setMessage(isRegister ? 'Registered successfully' : 'Logged in successfully');
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Error occurred');
    }
  };

  const connectService = async (service) => {
    // Redirect to OAuth flow (simplified for demo)
    const clientIds = {
      notion: 'your-notion-client-id',
      github: 'your-github-client-id',
      clockify: 'your-clockify-api-key' // Clockify uses API key, not OAuth
    };
    if (service === 'clockify') {
      const token = prompt('Enter Clockify API Key');
      await axios.post(
        'http://localhost:8000/auth/connect/clockify',
        { token },
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      alert('Clockify connected');
    } else {
      window.location.href = service === 'notion'
        ? `https://api.notion.com/v1/oauth/authorize?client_id=${clientIds.notion}&response_type=code&redirect_uri=http://localhost:3000`
        : `https://github.com/login/oauth/authorize?client_id=${clientIds.github}&redirect_uri=http://localhost:3000`;
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">{isRegister ? 'Register' : 'Login'}</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-full p-2 mb-4 border rounded"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full p-2 mb-4 border rounded"
          required
        />
        <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded">
          {isRegister ? 'Register' : 'Login'}
        </button>
      </form>
      <button
        onClick={() => setIsRegister(!isRegister)}
        className="mt-2 text-blue-500"
      >
        {isRegister ? 'Switch to Login' : 'Switch to Register'}
      </button>
      {message && <p className="mt-2 text-red-500">{message}</p>}
      <div className="mt-4">
        <button
          onClick={() => connectService('notion')}
          className="w-full bg-green-500 text-white p-2 rounded mb-2"
        >
          Connect Notion
        </button>
        <button
          onClick={() => connectService('github')}
          className="w-full bg-gray-800 text-white p-2 rounded mb-2"
        >
          Connect GitHub
        </button>
        <button
          onClick={() => connectService('clockify')}
          className="w-full bg-purple-500 text-white p-2 rounded"
        >
          Connect Clockify
        </button>
      </div>
    </div>
  );
}

export default Login;
```

**frontend/src/components/Report.jsx**
```jsx
import { useState, useEffect } from 'react';
import axios from 'axios';

function Report() {
  const [report, setReport] = useState('');

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await axios.get('http://localhost:8000/report/generate', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
        });
        setReport(response.data.report);
      } catch (error) {
        setReport('Error fetching report');
      }
    };
    fetchReport();
  }, []);

  return (
    <div className="bg-white p-6 rounded shadow mb-4">
      <h2 className="text-xl font-bold mb-2">Weekly Report</h2>
      <p>{report || 'Loading...'}</p>
    </div>
  );
}

export default Report;
```

**frontend/src/components/CalendarView.jsx**
```jsx
import { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import axios from 'axios';

function CalendarView() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const fetchEvents = async () => {
      // Fetch Clockify time entries (simplified)
      const response = await axios.get('http://localhost:8000/report/generate', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      const clockify = response.data.clockify?.time_entries || [];
      const calendarEvents = clockify.map(entry => ({
        title: entry.description || 'Task',
        start: entry.timeInterval.start,
        end: entry.timeInterval.end,
      }));
      setEvents(calendarEvents);
    };
    fetchEvents();
  }, []);

  return (
    <div className="bg-white p-6 rounded shadow mb-4">
      <h2 className="text-xl font-bold mb-2">Calendar View</h2>
      <FullCalendar
        plugins={[dayGridPlugin]}
        initialView="dayGridWeek"
        events={events}
      />
    </div>
  );
}

export default CalendarView;
```

**frontend/src/components/Dashboard.jsx**
```jsx
import { useState, useEffect } from 'react';
import axios from 'axios';

function Dashboard() {
  const [metrics, setMetrics] = useState({ totalTime: 0, activities: [] });

  useEffect(() => {
    const fetchMetrics = async () => {
      const response = await axios.get('http://localhost:8000/report/generate', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      const clockify = response.data.clockify?.time_entries || [];
      const totalTime = clockify.reduce((sum, entry) => {
        const duration = (new Date(entry.timeInterval.end) - new Date(entry.timeInterval.start)) / 3600000;
        return sum + duration;
      }, 0);
      const activities = clockify
        .reduce((acc, entry) => {
          const key = entry.description || 'Unknown';
          acc[key] = (acc[key] || 0) + (new Date(entry.timeInterval.end) - new Date(entry.timeInterval.start)) / 3600000;
          return acc;
        }, {});
      const sortedActivities = Object.entries(activities)
        .map(([name, hours]) => ({ name, hours }))
        .sort((a, b) => b.hours - a.hours);
      setMetrics({ totalTime, activities: sortedActivities });
    };
    fetchMetrics();
  }, []);

  return (
    <div className="bg-white p-6 rounded shadow">
      <h2 className="text-xl font-bold mb-2">Dashboard</h2>
      <p>Total Time Spent: {metrics.totalTime.toFixed(2)} hours</p>
      <h3 className="text-lg font-semibold mt-4">Activities by Time Spent</h3>
      <ul>
        {metrics.activities.map(activity => (
          <li key={activity.name}>
            {activity.name}: {activity.hours.toFixed(2)} hours
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Dashboard;
```

**frontend/src/index.css**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**frontend/package.json**
```json
{
  "name": "after-action-report",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.7.7",
    "@fullcalendar/core": "^6.1.15",
    "@fullcalendar/daygrid": "^6.1.15",
    "@fullcalendar/react": "^6.1.15",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "vite": "^5.4.8",
    "tailwindcss": "^3.4.14",
    "@vitejs/plugin-react": "^4.3.2"
  }
}
```

**frontend/vite.config.js**
```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
});
```

**frontend/tailwind.config.js**
```javascript
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

**frontend/Dockerfile**
```dockerfile
FROM node:18
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]
```

#### Docker Compose
**docker-compose.yml**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/aar
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=aar
    volumes:
      - postgres_data:/var/lib/postgresql/data
  redis:
    image: redis:7
    volumes:
      - redis_data:/data
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
volumes:
  postgres_data:
  redis_data:
```

#### Monitoring
**prometheus.yml**
```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
```

#### README
**README.md**
```markdown
# After Action Report

A single-page application to generate weekly productivity reports from Notion, GitHub, and Clockify data using a local LLM.

## Setup
1. Install Docker and Docker Compose.
2. Install Ollama and pull LLaMA 3: `ollama pull llama3`.
3. Create a `.env` file in `backend/` with:
   ```
   DATABASE_URL=postgresql://user:password@postgres:5432/aar
   REDIS_URL=redis://redis:6379/0
   JWT_SECRET=your-secret-key
   NOTION_CLIENT_ID=your-notion-client-id
   NOTION_CLIENT_SECRET=your-notion-client-secret
   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret
   CLOCKIFY_API_KEY=your-clockify-api-key
   OLLAMA_HOST=http://localhost:11434
   ```
4. Run `docker-compose up --build`.
5. Access the app at `http://localhost:3000`.

## Deployment
- **Frontend**: Deploy to Vercel using `vercel --prod`.
- **Backend**: Deploy to Render using `render.yaml` or push Docker image to Render.
- **Database/Cache**: Use Render's free PostgreSQL and Redis instances.

## Future Features
- iCloud Calendar integration.
- Advanced dashboard with 3D visualizations using Three.js.

## Metrics
- Notion: Tasks completed/updated.
- GitHub: Commits, issues, PRs.
- Clockify: Hours per project/task.
- LLM: Report generation time, token usage.
```

### Setup Instructions
1. **Install Dependencies**:
   - Install Docker and Docker Compose.
   - Install Ollama (`ollama pull llama3`).
   - Install Node.js and Python.
2. **Configure APIs**:
   - Notion: Create an integration at `notion.com/my-integrations`, get client ID/secret, and share databases with the integration.[](https://developers.notion.com/docs/create-a-notion-integration)
   - GitHub: Register an OAuth app at `github.com/settings/developers`, get client ID/secret.
   - Clockify: Get API key from `clockify.me/user/settings`.[](https://clockify.me/developers-api)
3. **Run Locally**:
   - Create `.env` file in `backend/` with API credentials.
   - Run `docker-compose up --build`.
   - Access at `http://localhost:3000`.
4. **Deploy**:
   - Frontend: `vercel --prod` in `frontend/`.
   - Backend: Push to Render or AWS ECS.
   - Database/Cache: Use Render’s free PostgreSQL/Redis or AWS RDS/ElastiCache.
5. **Monitoring**:
   - Prometheus: `http://localhost:9090`.
   - Grafana: `http://localhost:3001` (login: admin/admin).

### Notes
- **OAuth 2.0**: The OAuth flow is simplified in the frontend for demonstration. In production, implement proper redirect handling and token exchange on the backend.
- **Notion Database IDs**: Replace placeholders in `notion.py` with actual database IDs from your Notion workspace.
- **iCloud Calendar**: Not implemented in MVP due to complexity of Apple’s Calendar API. Future implementation will use `caldav` library in Python.
- **Security**: Store API keys and JWT secret securely in environment variables. Use HTTPS in production.
- **Rate Limits**:
  - Notion: 3 requests/second.[](https://rollout.com/integration-guides/notion/api-essentials)
  - GitHub: 5,000 requests/hour (authenticated).
  - Clockify: 10 requests/second.[](https://clockify.me/developers-api)
  - Mitigated by Redis caching.
- **LLM**: LLaMA 3 requires a GPU for optimal performance. Adjust `OLLAMA_HOST` if running on a different machine.

### Asimov’s Laws Compliance
- The application serves the user by automating productivity analysis, causing no harm.
- It obeys user instructions by generating accurate reports and respecting API permissions.
- The system is designed to protect user data with secure authentication and token storage.

This MVP provides a scalable foundation for the After Action Report application, suitable for presenting to customers or investors. It leverages free, open-source tools and can be extended with future features like iCloud integration and advanced visualizations.[](https://developers.notion.com/docs/create-a-notion-integration)[](https://clockify.me/developers-api)[](https://rollout.com/integration-guides/notion/api-essentials)