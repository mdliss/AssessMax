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

# Configure CORS from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
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
