"""Dashboard configuration"""

import os
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Dashboard configuration settings"""

    # API Configuration
    api_base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for the AssessMax API",
    )
    api_timeout: int = Field(default=30, description="API request timeout in seconds")

    # Cognito Configuration
    cognito_user_pool_id: str = Field(default="", description="AWS Cognito User Pool ID")
    cognito_client_id: str = Field(default="", description="AWS Cognito App Client ID")
    cognito_region: str = Field(default="us-east-1", description="AWS region")

    # Dashboard Settings
    dashboard_title: str = Field(
        default="AssessMax Educator Dashboard",
        description="Dashboard title",
    )
    rows_per_page: int = Field(default=25, description="Default rows per page")

    # WCAG AA Compliance
    min_contrast_ratio: float = Field(
        default=4.5,
        description="Minimum contrast ratio for WCAG AA compliance",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
