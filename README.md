# Chat Application Backend

A real-time chat application backend built with Python and FastAPI.

## Overview

This project implements a backend for a real-time chat application using FastAPI, SQLModel for ORM, PostgreSQL for database, and JWT for authentication.

## Task 1: Environment & Dependencies Setup

### Prerequisites
- Python 3.10+
- PostgreSQL
- Git

### Setup Instructions

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd ChatApplication
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Dependencies
The following packages are pinned in `requirements.txt`:
pip install -r requirement.txt

### Running the Application
To start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### API Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

### Project Structure
```
ChatApplication/
├── app/
│   ├── __init__.py
│   └── main.py          # FastAPI application
├── venv/                # Virtual environment
├── requirements.txt     # Dependencies
└── README.md           # This file
```# Chat Application Backend

## Screenshots

![App Running](images/app-running.png)
*Screenshot of the FastAPI app running with uvicorn.*

## Task 2: JWT Authentication & Role-Based Access Control (RBAC)

### Overview
Implemented a secure authentication system with user roles using JWT tokens and role-based access control.

### User Model
- **Fields**: id, username, email, hashed_password, role
- **Roles**: admin, user (default)
- **Database**: SQLModel with SQLAlchemy ORM

### Authentication Endpoints

#### POST /auth/signup
Creates a new user account with hashed password and assigned role.

**Request Body**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "user"  // optional, defaults to "user"
}
```

**Response**:
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "role": "user"
}
```

#### POST /auth/login
Authenticates user and returns JWT access token.

**Request Body** (form data):
```
username: string
password: string
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### JWT Token Features
- **Algorithm**: HS256
- **Expiry**: 30 minutes
- **Payload**: Contains username and role
- **Security**: Passwords hashed with bcrypt

### Role-Based Access Control
Implemented reusable FastAPI dependencies for role checking:

- `require_admin`: Restricts access to admin users only
- `require_user`: Allows any authenticated user
- `get_current_user`: Returns current authenticated user

### Protected Routes

#### GET /protected/admin
- **Access**: Admin users only
- **Response**: `{"message": "Hello {username}, you are an admin!"}`

#### GET /protected/user
- **Access**: Any authenticated user
- **Response**: `{"message": "Hello {username}, you are authenticated!"}`

### Usage Example
```bash
# 1. Signup
curl -X POST "http://127.0.0.1:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@example.com","password":"password","role":"admin"}'

# 2. Login
curl -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password"

# 3. Access protected route
curl -X GET "http://127.0.0.1:8000/protected/admin" \
  -H "Authorization: Bearer {access_token}"
```

### Security Features
- Passwords are never stored in plain text
- JWT tokens include expiry timestamps
- Role checks are enforced via dependencies, not hardcoded
- Secure password hashing using bcrypt
- Token-based authentication with Bearer scheme

