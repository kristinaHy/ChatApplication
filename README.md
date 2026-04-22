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

