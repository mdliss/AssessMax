# Authentication Setup Guide

## Overview

AssessMax uses AWS Cognito for authentication with JWT token validation and role-based access control (RBAC).

## Architecture

```
Client → AWS Cognito (Auth) → JWT Token → FastAPI (Verify) → Protected Endpoints
```

## User Roles

1. **Educator** (`educator`) - Can upload transcripts, view assessments, export data
2. **Admin** (`admin`) - Full access to all endpoints including user management
3. **Read-Only** (`read_only`) - View-only access to dashboards and reports

## AWS Cognito Setup

### 1. Create User Pool

```bash
# Using AWS CLI
aws cognito-idp create-user-pool \
    --pool-name assessmax-users \
    --policies "PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=false}" \
    --auto-verified-attributes email \
    --mfa-configuration OFF \
    --region us-east-1
```

### 2. Create User Pool Client

```bash
aws cognito-idp create-user-pool-client \
    --user-pool-id <USER_POOL_ID> \
    --client-name assessmax-api \
    --generate-secret \
    --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
    --region us-east-1
```

### 3. Create User Groups

```bash
# Create educator group
aws cognito-idp create-group \
    --user-pool-id <USER_POOL_ID> \
    --group-name educator \
    --description "Educators with upload and view permissions" \
    --region us-east-1

# Create admin group
aws cognito-idp create-group \
    --user-pool-id <USER_POOL_ID> \
    --group-name admin \
    --description "Administrators with full access" \
    --region us-east-1

# Create read_only group
aws cognito-idp create-group \
    --user-pool-id <USER_POOL_ID> \
    --group-name read_only \
    --description "Read-only users" \
    --region us-east-1
```

### 4. Configure Environment Variables

Update `.env` file:

```bash
# AWS Cognito
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_CLIENT_ID=your_client_id_here
COGNITO_CLIENT_SECRET=your_client_secret_here
COGNITO_DOMAIN=assessmax-auth.auth.us-east-1.amazoncognito.com

# Optional: Set custom JWKS URL
# COGNITO_JWKS_URL=https://cognito-idp.us-east-1.amazonaws.com/{pool_id}/.well-known/jwks.json

# JWT Configuration
JWT_AUDIENCE=your_client_id_here  # Usually same as COGNITO_CLIENT_ID
```

## Usage

### 1. Authenticating Users

```bash
# Login with email/password
curl -X POST https://cognito-idp.us-east-1.amazonaws.com/ \
  -H "Content-Type: application/x-amz-json-1.1" \
  -H "X-Amz-Target: AWSCognitoIdentityProviderService.InitiateAuth" \
  -d '{
    "AuthFlow": "USER_PASSWORD_AUTH",
    "ClientId": "<CLIENT_ID>",
    "AuthParameters": {
      "USERNAME": "educator@example.com",
      "PASSWORD": "SecurePass123"
    }
  }'
```

Response includes `IdToken` which is used for API authentication.

### 2. Making Authenticated Requests

```bash
# Get user info
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <ID_TOKEN>"

# Access educator endpoint
curl -X GET http://localhost:8000/auth/educator-only \
  -H "Authorization: Bearer <ID_TOKEN>"

# Access admin endpoint (requires admin role)
curl -X GET http://localhost:8000/auth/admin-only \
  -H "Authorization: Bearer <ID_TOKEN>"
```

### 3. Using in FastAPI Endpoints

```python
from typing import Annotated
from fastapi import Depends
from app.auth import TokenData, get_current_user, require_admin, UserRole

# Require authentication
@app.get("/protected")
async def protected_route(user: Annotated[TokenData, Depends(get_current_user)]):
    return {"user_id": user.sub}

# Require specific role
@app.delete("/admin/resource")
async def admin_only(user: Annotated[TokenData, Depends(require_admin)]):
    return {"message": "Admin access granted"}

# Custom role check
@app.post("/custom")
async def custom_roles(
    user: Annotated[TokenData, Depends(require_role(UserRole.ADMIN, UserRole.EDUCATOR))]
):
    return {"message": "Access granted"}
```

## JWT Token Structure

```json
{
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "email": "educator@example.com",
  "cognito:username": "educator",
  "cognito:groups": ["educator"],
  "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXXXXXX",
  "aud": "your_client_id",
  "exp": 1234567890
}
```

## Security Features

1. **JWT Signature Verification** - Uses Cognito's public JWKS
2. **Token Expiration** - Validates exp claim
3. **Audience Validation** - Ensures token is for this app
4. **JWKS Caching** - 1-hour TTL to reduce latency
5. **Role-Based Access** - Granular permission control
6. **HTTP-Only Cookies** - Session security (when implemented in frontend)

## Testing

Run authentication tests:

```bash
cd backend
pytest tests/test_auth.py -v
```

## Troubleshooting

### Token Validation Fails

1. Check JWKS URL is correct
2. Verify COGNITO_USER_POOL_ID matches token issuer
3. Ensure JWT_AUDIENCE matches client ID
4. Check token hasn't expired

### Role Not Working

1. Verify user is assigned to correct Cognito group
2. Check group name matches exactly (case-sensitive)
3. Ensure user re-authenticates after group assignment

### CORS Issues

Update `ALLOWED_ORIGINS` in `.env`:

```bash
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

## Future Enhancements

- [ ] Google OAuth integration
- [ ] SAML SSO for enterprise customers
- [ ] Multi-factor authentication (MFA)
- [ ] Session refresh token rotation
- [ ] API key authentication for service accounts
