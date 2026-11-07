"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from typing import NamedTuple

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

SESSION_DURATION_SECONDS = 8 * 60 * 60
bearer_scheme = HTTPBearer(auto_error=False)


class TeacherSession(NamedTuple):
    token_hash: str
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


active_sessions: dict[str, tuple[str, float]] = {}


def get_teacher_credentials() -> dict[str, str]:
    configured_credentials = os.getenv("TEACHER_CREDENTIALS_JSON")
    if not configured_credentials:
        raise HTTPException(
            status_code=503,
            detail="Teacher login is not configured."
        )

    try:
        credentials = json.loads(configured_credentials)
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=503,
            detail="Teacher login configuration is invalid."
        ) from error

    if (
        not isinstance(credentials, dict)
        or not credentials
        or any(
            not isinstance(username, str)
            or not username
            or not isinstance(password, str)
            or not password
            for username, password in credentials.items()
        )
    ):
        raise HTTPException(
            status_code=503,
            detail="Teacher login configuration is invalid."
        )

    return credentials


def require_teacher(
    authorization: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TeacherSession:
    if authorization is None or authorization.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Teacher login required")

    token_hash = hashlib.sha256(
        authorization.credentials.encode("utf-8")
    ).hexdigest()
    session = active_sessions.get(token_hash)
    if session is None:
        raise HTTPException(status_code=401, detail="Teacher session is invalid")

    username, expires_at = session
    if expires_at <= time.time():
        del active_sessions[token_hash]
        raise HTTPException(status_code=401, detail="Teacher session has expired")

    return TeacherSession(token_hash, username)


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(request: LoginRequest):
    configured_credentials = get_teacher_credentials()
    authenticated_username = None

    for username, password in configured_credentials.items():
        username_matches = hmac.compare_digest(
            request.username.encode("utf-8"),
            username.encode("utf-8"),
        )
        password_matches = hmac.compare_digest(
            request.password.encode("utf-8"),
            password.encode("utf-8"),
        )
        if username_matches and password_matches:
            authenticated_username = username

    if authenticated_username is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    for token_hash, (_, expires_at) in list(active_sessions.items()):
        if expires_at <= time.time():
            del active_sessions[token_hash]

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    active_sessions[token_hash] = (
        authenticated_username,
        time.time() + SESSION_DURATION_SECONDS,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": SESSION_DURATION_SECONDS,
    }


@app.post("/auth/logout")
def logout(teacher: TeacherSession = Depends(require_teacher)):
    active_sessions.pop(teacher.token_hash, None)
    return {"message": "Logged out"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    _: TeacherSession = Depends(require_teacher),
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    _: TeacherSession = Depends(require_teacher),
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
