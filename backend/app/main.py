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
