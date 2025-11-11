"""JWT verification for AWS Cognito tokens"""

import time
from typing import Any

import jwt
import requests
from jose import JWTError, jwk
from jose.utils import base64url_decode

from app.auth.models import AuthError, TokenData, UserRole
from app.config import settings

# Cache for JWKS keys with TTL
_jwks_cache: dict[str, Any] = {}
_jwks_cache_time: float = 0
_jwks_cache_ttl: int = 3600  # 1 hour


def get_jwks() -> dict[str, Any]:
    """
    Fetch and cache Cognito JWKS (JSON Web Key Set).

    Returns:
        dict: JWKS data containing public keys for token verification

    Raises:
        AuthError: If JWKS fetch fails
    """
    global _jwks_cache, _jwks_cache_time

    # Return cached JWKS if still valid
    current_time = time.time()
    if _jwks_cache and (current_time - _jwks_cache_time) < _jwks_cache_ttl:
        return _jwks_cache

    # Fetch fresh JWKS
    if not settings.cognito_jwks_url:
        # Construct JWKS URL from user pool ID and region
        jwks_url = (
            f"https://cognito-idp.{settings.aws_region}.amazonaws.com/"
            f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
        )
    else:
        jwks_url = settings.cognito_jwks_url

    try:
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_cache_time = current_time
        return _jwks_cache
    except requests.RequestException as e:
        raise AuthError(f"Failed to fetch JWKS: {str(e)}", status_code=500)


def verify_cognito_token(token: str) -> TokenData:
    """
    Verify and decode a Cognito JWT token.

    Args:
        token: JWT token string from Authorization header

    Returns:
        TokenData: Decoded and validated token data

    Raises:
        AuthError: If token is invalid, expired, or verification fails
    """
    try:
        # Get token headers
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")

        if not kid:
            raise AuthError("Token missing 'kid' header")

        # Get JWKS and find matching key
        jwks = get_jwks()
        key = None
        for jwk_key in jwks.get("keys", []):
            if jwk_key["kid"] == kid:
                key = jwk_key
                break

        if not key:
            raise AuthError("Public key not found in JWKS")

        # Construct public key
        public_key = jwk.construct(key)

        # Decode message
        message, encoded_signature = token.rsplit(".", 1)
        decoded_signature = base64url_decode(encoded_signature.encode())

        # Verify signature
        if not public_key.verify(message.encode(), decoded_signature):
            raise AuthError("Signature verification failed")

        # Decode token payload
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.jwt_audience or settings.cognito_client_id,
            options={"verify_exp": True},
        )

        # Extract user data
        sub = payload.get("sub")
        email = payload.get("email", "")
        username = payload.get("cognito:username") or email.split("@")[0]

        # Extract roles from Cognito groups
        cognito_groups = payload.get("cognito:groups", [])
        roles: list[UserRole] = []

        for group in cognito_groups:
            group_lower = group.lower()
            if group_lower == "admin":
                roles.append(UserRole.ADMIN)
            elif group_lower == "educator":
                roles.append(UserRole.EDUCATOR)
            elif group_lower in ["read_only", "readonly"]:
                roles.append(UserRole.READ_ONLY)

        # Default to educator if no roles assigned
        if not roles:
            roles.append(UserRole.EDUCATOR)

        return TokenData(
            sub=sub,
            email=email,
            username=username,
            roles=roles,
            cognito_groups=cognito_groups,
        )

    except JWTError as e:
        raise AuthError(f"Token validation failed: {str(e)}")
    except KeyError as e:
        raise AuthError(f"Token missing required field: {str(e)}")
    except Exception as e:
        raise AuthError(f"Token verification error: {str(e)}")


def clear_jwks_cache() -> None:
    """Clear the JWKS cache (useful for testing or manual refresh)"""
    global _jwks_cache, _jwks_cache_time
    _jwks_cache = {}
    _jwks_cache_time = 0
