import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from app.config import settings
from app.api import api_router

app = FastAPI(
    title="FinanceMaxAI API",
    description="Financial education platform API",
    version="1.0.0"
)

# Custom middleware to handle trailing slashes consistently
class TrailingSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        url_path = request.url.path
        # Only add trailing slash for GET requests on list endpoints (e.g., /users, /recommendations)
        # Don't add for POST/PUT/DELETE or detail endpoints (e.g., /message, /users/123)
        if (request.method == "GET" and
            not url_path.endswith("/") and
            "." not in url_path.split("/")[-1] and
            len(url_path.split("/")) <= 4):  # Only for short paths like /api/v1/users
            scope = request.scope
            scope["path"] = url_path + "/"
            request = Request(scope, request.receive)

        response = await call_next(request)
        return response

# CORS middleware (must be added before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://localhost:3002",
        "https://frontend-ten-chi-27.vercel.app",
        "https://frontend-7w28jda22-max-liss-projects.vercel.app",
        "https://frontend-bky8pef7o-max-liss-projects.vercel.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add trailing slash middleware
app.add_middleware(TrailingSlashMiddleware)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "FinanceMaxAI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health/")
async def health_check():
    return {"status": "healthy"}

@app.get("/status/dataset")
async def dataset_status():
    """Check if full dataset generation is complete"""
    import os
    import asyncio
    from app.database import get_db
    from sqlalchemy import select, func
    from app.models import User

    flag_exists = os.path.exists("/app/data/full_dataset.flag")
    log_exists = os.path.exists("/tmp/dataset_generation.log")

    # Count users in database
    async for session in get_db():
        result = await session.execute(select(func.count(User.user_id)))
        user_count = result.scalar()
        break

    # Read last few lines of log if it exists
    recent_logs = []
    if log_exists:
        try:
            with open("/tmp/dataset_generation.log", "r") as f:
                lines = f.readlines()
                recent_logs = [line.strip() for line in lines[-10:]]
        except:
            pass

    status = "complete" if flag_exists else ("generating" if log_exists else "not_started")

    expected_users = int(os.getenv("DATASET_USER_COUNT", "150"))
    return {
        "status": status,
        "flag_file_exists": flag_exists,
        "user_count": user_count,
        "expected_users": expected_users,
        "is_complete": flag_exists,
        "recent_logs": recent_logs
    }
