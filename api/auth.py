from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from .config import settings

# Simple API Key authentication for demo
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key authentication"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return {"api_key": api_key}

async def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    """Verify Bearer token authentication (alternative to API key)"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Simple token validation - in production use JWT
    if credentials.credentials != settings.secret_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return {"token": credentials.credentials}

# Optional authentication - allows both API key and bearer token
async def optional_auth(
    api_key: str = Security(api_key_header), 
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """Optional authentication - allows unauthenticated access"""
    if api_key == settings.api_key:
        return {"method": "api_key", "authenticated": True}
    elif credentials and credentials.credentials == settings.secret_key:
        return {"method": "bearer", "authenticated": True}
    else:
        return {"method": "none", "authenticated": False}

# Required authentication - must have valid API key or bearer token
async def require_auth(
    api_key: str = Security(api_key_header), 
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """Require authentication - either API key or bearer token"""
    if api_key and api_key == settings.api_key:
        return {"method": "api_key", "authenticated": True}
    elif credentials and credentials.credentials == settings.secret_key:
        return {"method": "bearer", "authenticated": True}
    else:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide either X-API-Key header or Bearer token.",
            headers={"WWW-Authenticate": "ApiKey, Bearer"}
        )