from fastapi import FastAPI

app = FastAPI(title="Chat Application API", version="1.0.0")


@app.get("/")
async def root():
    """Root endpoint for the chat application."""
    return {"message": "Welcome to Chat Application API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
