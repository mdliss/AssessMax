"""Authentication module for AWS Cognito integration"""

from app.auth.dependencies import (
    get_current_user,
    get_optional_user,
    require_admin,
    require_educator,
    require_role,
)
from app.auth.jwt import verify_cognito_token
from app.auth.models import AuthError, TokenData, UserRole

__all__ = [
    "get_current_user",
    "get_optional_user",
    "require_role",
    "require_admin",
    "require_educator",
    "TokenData",
    "UserRole",
    "AuthError",
    "verify_cognito_token",
]
