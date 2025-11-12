"""Main FastAPI application entry point"""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import __version__
from app.assessments import router as assessments_router
from app.auth import TokenData, get_current_user, require_admin, require_educator
from app.config import settings
from app.ingest import router as ingest_router
from app.jobs import router as jobs_router

app = FastAPI(
    title="AssessMax API",
    description="Middle School Non-Academic Skills Measurement Engine",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
app.include_router(ingest_router)
app.include_router(jobs_router)
app.include_router(assessments_router)

# Configure CORS with dynamic origin handling
def get_allowed_origins():
    """Get list of allowed origins, expanding wildcards"""
    origins = []
    for origin in settings.allowed_origins:
        # Keep non-wildcard origins as-is
        if "*" not in origin:
            origins.append(origin)
        # For Railway wildcard, we'll handle it in origin validation
    return origins if origins else ["*"]

# Custom CORS origin validator for Railway domains
def is_allowed_origin(origin: str) -> bool:
    """Check if origin is allowed, supporting Railway wildcard patterns"""
    # Check exact matches first
    if origin in settings.allowed_origins:
        return True

    # Check wildcard patterns
    for allowed in settings.allowed_origins:
        if "*" in allowed:
            # Convert wildcard pattern to regex-like check
            # e.g., "https://*.up.railway.app" -> check if ends with ".up.railway.app"
            pattern = allowed.replace("https://", "").replace("http://", "")
            if pattern.startswith("*."):
                domain_suffix = pattern[1:]  # Remove the "*"
                origin_domain = origin.replace("https://", "").replace("http://", "")
                if origin_domain.endswith(domain_suffix):
                    return True

    return False

# Use allow_origin_regex for Railway domains or custom validator
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=r"https://.*\.up\.railway\.app",  # Allow all Railway apps
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    version: str
    service: str


@app.get("/healthz", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint for service monitoring.

    Returns:
        HealthResponse: Service health status and metadata
    """
    return HealthResponse(
        status="healthy",
        version=__version__,
        service="assessmax-backend",
    )


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information"""
    return {
        "service": "AssessMax API",
        "version": __version__,
        "docs": "/docs",
        "health": "/healthz",
        "auth": "AWS Cognito",
    }


class UserInfoResponse(BaseModel):
    """User information response"""

    user_id: str
    email: str
    username: str
    display_name: str
    roles: list[str]
    is_admin: bool
    is_educator: bool


@app.get("/auth/me", response_model=UserInfoResponse, tags=["Authentication"])
async def get_user_info(
    user: Annotated[TokenData, Depends(get_current_user)]
) -> UserInfoResponse:
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.

    Returns:
        UserInfoResponse: Current user details and roles
    """
    return UserInfoResponse(
        user_id=user.sub,
        email=user.email,
        username=user.username,
        display_name=user.display_name,
        roles=[role.value for role in user.roles],
        is_admin=user.is_admin,
        is_educator=user.is_educator,
    )


@app.get("/auth/educator-only", tags=["Authentication"])
async def educator_only_endpoint(
    user: Annotated[TokenData, Depends(require_educator)]
) -> dict[str, str]:
    """
    Example endpoint requiring educator or admin role.

    Returns:
        dict: Success message with user info
    """
    return {
        "message": "Access granted to educator area",
        "user": user.display_name,
        "roles": [role.value for role in user.roles],
    }


@app.get("/auth/admin-only", tags=["Authentication"])
async def admin_only_endpoint(
    user: Annotated[TokenData, Depends(require_admin)]
) -> dict[str, str]:
    """
    Example endpoint requiring admin role only.

    Returns:
        dict: Success message with user info
    """
    return {
        "message": "Access granted to admin area",
        "user": user.display_name,
        "roles": [role.value for role in user.roles],
    }
