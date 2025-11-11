"""Authentication and session management"""

from typing import Any

import requests
import streamlit as st

from config import settings


class AuthManager:
    """Manage authentication state and API requests"""

    @staticmethod
    def get_token() -> str | None:
        """Get the current auth token from session state"""
        return st.session_state.get("auth_token")

    @staticmethod
    def set_token(token: str) -> None:
        """Set the auth token in session state"""
        st.session_state.auth_token = token

    @staticmethod
    def clear_token() -> None:
        """Clear the auth token from session state"""
        if "auth_token" in st.session_state:
            del st.session_state.auth_token

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return "auth_token" in st.session_state and st.session_state.auth_token is not None

    @staticmethod
    def get_headers() -> dict[str, str]:
        """Get headers for API requests with auth token"""
        token = AuthManager.get_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    @staticmethod
    def api_get(endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Make authenticated GET request to API

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            Exception: If request fails
        """
        url = f"{settings.api_base_url}{endpoint}"
        response = requests.get(
            url,
            headers=AuthManager.get_headers(),
            params=params or {},
            timeout=settings.api_timeout,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_user_info() -> dict[str, Any] | None:
        """Get current user information"""
        try:
            return AuthManager.api_get("/auth/me")
        except Exception:
            return None

    @staticmethod
    def login(username: str, password: str) -> bool:
        """
        Authenticate user with username and password

        Args:
            username: User's username
            password: User's password

        Returns:
            True if login successful, False otherwise
        """
        # For MVP, we'll use a mock token for demo purposes
        # In production, this would call AWS Cognito
        if username and password:
            # Mock token for development
            mock_token = f"mock_token_{username}"
            AuthManager.set_token(mock_token)
            return True
        return False

    @staticmethod
    def logout() -> None:
        """Log out current user"""
        AuthManager.clear_token()
        st.rerun()
