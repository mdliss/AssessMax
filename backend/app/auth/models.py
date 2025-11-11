"""Authentication models and enums"""

from enum import Enum

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User roles for role-based access control"""

    EDUCATOR = "educator"
    ADMIN = "admin"
    READ_ONLY = "read_only"


class TokenData(BaseModel):
    """
    Decoded JWT token data from AWS Cognito.

    Attributes:
        sub: Subject (user ID) from Cognito
        email: User's email address
        username: Username or email local part
        roles: List of assigned roles from Cognito groups
        cognito_groups: Raw Cognito group membership
    """

    sub: str = Field(..., description="Cognito user ID (UUID)")
    email: str = Field(..., description="User email address")
    username: str = Field(..., description="Display username")
    roles: list[UserRole] = Field(default_factory=list, description="Assigned roles")
    cognito_groups: list[str] = Field(
        default_factory=list, description="Raw Cognito groups"
    )

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return UserRole.ADMIN in self.roles

    @property
    def is_educator(self) -> bool:
        """Check if user has educator role"""
        return UserRole.EDUCATOR in self.roles

    @property
    def is_read_only(self) -> bool:
        """Check if user has read-only role"""
        return UserRole.READ_ONLY in self.roles

    @property
    def display_name(self) -> str:
        """
        Get display name for the user.

        Returns username truncated to 40 characters with ellipsis if needed.
        """
        if len(self.username) <= 40:
            return self.username
        return self.username[:37] + "..."


class AuthError(Exception):
    """Custom exception for authentication errors"""

    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
