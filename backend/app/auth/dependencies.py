"""FastAPI dependencies for authentication and authorization"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import verify_cognito_token
from app.auth.models import AuthError, TokenData, UserRole
from app.config import settings

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> TokenData:
    """
    FastAPI dependency to get the current authenticated user.

    Validates JWT token from Authorization header and returns user data.

    Args:
        credentials: HTTP Bearer credentials containing JWT token

    Returns:
        TokenData: Validated user information

    Raises:
        HTTPException: 401 if token is invalid or missing

    Example:
        ```python
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.sub, "email": user.email}
        ```
    """
    token = credentials.credentials

    # Bypass auth for development/testing
    if settings.bypass_auth:
        # Extract username from mock token format: "mock_token_{username}"
        if token.startswith("mock_token_"):
            username = token.replace("mock_token_", "")
            return TokenData(
                sub=f"mock-user-{username}",
                email=f"{username}@example.com",
                username=username,
                roles=[UserRole.ADMIN],  # Give admin role for dev
                cognito_groups=["admin"],
            )

    try:
        user_data = verify_cognito_token(token)
        return user_data
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*allowed_roles: UserRole):
    """
    Create a dependency that requires specific roles.

    Args:
        *allowed_roles: One or more UserRole values that are allowed

    Returns:
        Dependency function that checks user roles

    Raises:
        HTTPException: 403 if user lacks required role

    Example:
        ```python
        @app.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: str,
            user: TokenData = Depends(require_role(UserRole.ADMIN))
        ):
            # Only admins can access this endpoint
            pass
        ```
    """

    async def role_checker(user: Annotated[TokenData, Depends(get_current_user)]) -> TokenData:
        """Check if user has required role"""
        if not any(role in user.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}",
            )
        return user

    return role_checker


# Convenience dependencies for common role checks
require_educator = require_role(UserRole.EDUCATOR, UserRole.ADMIN)
require_admin = require_role(UserRole.ADMIN)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    )
) -> TokenData | None:
    """
    FastAPI dependency for optional authentication.

    Returns user data if valid token provided, None otherwise.
    Useful for endpoints that have different behavior for authenticated users.

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        TokenData | None: User data if authenticated, None otherwise

    Example:
        ```python
        @app.get("/content")
        async def get_content(user: TokenData | None = Depends(get_optional_user)):
            if user:
                # Return personalized content
                return {"message": f"Hello {user.username}"}
            # Return public content
            return {"message": "Hello guest"}
        ```
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Bypass auth for development/testing
    if settings.bypass_auth and token.startswith("mock_token_"):
        username = token.replace("mock_token_", "")
        return TokenData(
            sub=f"mock-user-{username}",
            email=f"{username}@example.com",
            username=username,
            roles=[UserRole.ADMIN],
            cognito_groups=["admin"],
        )

    try:
        user_data = verify_cognito_token(token)
        return user_data
    except AuthError:
        return None
