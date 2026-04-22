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
Implemented JWT-based authentication with role-based access control using FastAPI dependencies. Users can register with a role, log in to receive a signed token, and access protected routes based on that role.

### User Model
The `User` model includes:
- `id`
- `username`
- `email`
- `hashed_password`
- `role`

Supported roles:
- `admin`
- `user`

Passwords are stored only as hashed values, never in plain text.

### Authentication Endpoints

#### `POST /auth/signup`
Creates a new user with a hashed password and assigned role.

**Request Body**
```json
{
  "username": "admin2",
  "email": "admin2@example.com",
  "password": "adminpass123",
  "role": "admin"
}
```

**Successful Response**
```json
{
  "id": 1,
  "username": "admin2",
  "email": "admin2@example.com",
  "role": "admin"
}
```

#### `POST /auth/login`
Authenticates a user and returns a JWT access token.

**Form Data**
```text
username=admin2
password=adminpass123
```

**Successful Response**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### JWT Details
- **Signing Algorithm:** `HS256`
- **Expiry:** Included in the token payload
- **Payload Fields:** `sub`, `role`, `exp`

Example payload:
```json
{
  "sub": "admin2",
  "role": "admin",
  "exp": 1776829485
}
```

### RBAC Dependency
Role checks are enforced using reusable dependencies in `app/dependencies.py`.

```python
def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

require_admin = require_role(UserRole.ADMIN)
```

### Demonstrated Protected Route
The RBAC dependency is used on this protected route in `app/main.py`:

```python
@app.get("/protected/admin")
async def admin_only(current_user: User = Depends(require_admin)):
    return {"message": f"Hello {current_user.username}, you are an admin!"}
```

This demonstrates the deliverable requirement of a reusable RBAC dependency used on a protected route.

### How Task 2 Was Tested

#### 1. Signup test
Used Swagger UI at `http://127.0.0.1:8000/docs` to call:

- `POST /auth/signup`

Example test body:
```json
{
  "username": "admin2",
  "email": "admin2@example.com",
  "password": "adminpass123",
  "role": "admin"
}
```

Expected result:
- user created successfully
- response returns `id`, `username`, `email`, and `role`

#### 2. Login test
Used Swagger UI to call:

- `POST /auth/login`

Example credentials:
```text
username: admin2
password: adminpass123
```

Expected result:
- HTTP `200 OK`
- JWT token returned in `access_token`

#### 3. Authenticated route test
Used the token returned by `/auth/login` and authenticated in Swagger using the **raw token only**.

Important:
- paste only the JWT token into Swagger Authorize
- do **not** type `Bearer ` manually, because Swagger adds it automatically

Then tested:
- `GET /protected/user` → should return `200 OK`
- `GET /protected/admin` → should return `200 OK` for admin users

#### 4. RBAC verification
The `require_admin` dependency protects `GET /protected/admin`.

Expected behavior:
- admin token → `200 OK`
- normal user token → `403 Forbidden`

### Deliverable
**Working `/signup` and `/login` endpoints, and a demonstrated RBAC dependency used on at least one protected route.**

### Task 2 Screenshots
![Task 2 Screenshot 1](images/task2.png)

![Task 2 Screenshot 2](images/task2.01.png)

![Task 2 Screenshot 3](images/task2.02.png)

![Task 2 Screenshot 4](images/task2.1.png)

![Task 2 Screenshot 5](images/task2.2.png)

![Task 2 Screenshot 6](images/task2.11.png)

![Task 2 Screenshot 7](images/task2.12.png)

![Task 2 Screenshot 8](images/task2.13.png)

![Task 2 Screenshot 9](images/task2u.png)

![Task 2 Screenshot 10](images/task2u1.png)

![Task 2 Screenshot 11](images/task2u2.png)

![Task 2 Screenshot 12](images/task2u3.png)
