# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities while logged in as a teacher
- Unregister students while logged in as a teacher
- Browse activities and participants without logging in

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Configure teacher credentials. Copy `.env.example` to `.env` in the repository root and replace the example username and password. Add one or more teacher accounts to the `TEACHER_CREDENTIALS_JSON` object. The `.env` file is git-ignored; never commit real credentials.

3. Run the application from the repository root. In VS Code, use the **Launch Mergington WebApp** configuration, which reads `.env`. From a terminal, load the variables and start Uvicorn:

   ```sh
   set -a
   . ./.env
   set +a
   python -m uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

Teacher credentials are provided through environment configuration instead of a checked-in password file. Teacher sessions are held in memory, expire after eight hours, and are cleared when the server restarts. The browser keeps the session token in memory only, so a page reload requires the teacher to log in again. Use HTTPS when exposing the app beyond localhost.

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| POST   | `/auth/login`                                                     | Sign in with a configured teacher username and password             |
| POST   | `/auth/logout`                                                    | End the current teacher session                                     |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity (teacher session required)                  |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher session required)                  |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
