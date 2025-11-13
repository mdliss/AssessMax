"""Application configuration using pydantic-settings"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AssessMax Backend"
    debug: bool = False
    log_level: str = "INFO"

    # AWS Configuration
    aws_region: str = Field(default="us-east-2", alias="AWS_REGION")
    aws_account_id: str = Field(default="", alias="AWS_ACCOUNT_ID")
    environment: str = Field(default="dev", alias="ENVIRONMENT")

    # AWS Cognito
    cognito_user_pool_id: str = Field(default="", alias="COGNITO_USER_POOL_ID")
    cognito_client_id: str = Field(default="", alias="COGNITO_CLIENT_ID")
    cognito_client_secret: str = Field(default="", alias="COGNITO_CLIENT_SECRET")
    cognito_domain: str = Field(default="", alias="COGNITO_DOMAIN")
    cognito_jwks_url: str = Field(default="", alias="COGNITO_JWKS_URL")
    jwt_audience: str = Field(default="", alias="JWT_AUDIENCE")

    # Database (RDS Postgres)
    database_url: str = Field(
        default="postgresql://user:pass@localhost:5432/assessmax",
        alias="DATABASE_URL",
    )
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="assessmax", alias="DB_NAME")
    db_user: str = Field(default="", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")

    # S3 Buckets
    s3_bucket_raw: str = Field(default="assessmax-raw", alias="S3_RAW_BUCKET")
    s3_bucket_normalized: str = Field(
        default="assessmax-normalized", alias="S3_NORMALIZED_BUCKET"
    )
    s3_bucket_outputs: str = Field(default="assessmax-outputs", alias="S3_OUTPUTS_BUCKET")

    # DynamoDB Tables
    dynamodb_jobs_table: str = Field(default="assessmax-jobs", alias="DYNAMO_JOBS_TABLE")
    dynamodb_artifacts_table: str = Field(
        default="assessmax-artifacts", alias="DYNAMO_ARTIFACTS_TABLE"
    )

    # File Upload Limits
    max_file_size_mb: int = Field(default=50, alias="MAX_FILE_SIZE_MB")
    max_concurrent_uploads: int = Field(default=2, alias="MAX_CONCURRENT_UPLOADS")

    # Security
    jwt_secret_key: str = Field(default="", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=60, alias="JWT_EXPIRATION_MINUTES")
    bypass_auth: bool = Field(default=False, alias="BYPASS_AUTH")

    # API Configuration
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    allowed_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "https://*.up.railway.app",  # Wildcard for all Railway apps
        ],
        alias="ALLOWED_ORIGINS",
    )


# Global settings instance
settings = Settings()
