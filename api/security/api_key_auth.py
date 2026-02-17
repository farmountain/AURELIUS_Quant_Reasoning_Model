"""
API Key Authentication and Rate Limiting for AURELIUS Primitives.

Provides dual authentication support:
- API keys for external developers (1000 requests/hour)
- JWT tokens for dashboard users (5000 requests/hour)

Rate limiting prevents abuse and ensures fair usage.
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from passlib.context import CryptContext
import time
from collections import defaultdict
import asyncio

# API key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

# Password hashing for API keys
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory rate limiting (production should use Redis)
_rate_limit_cache: Dict[str, Dict[str, any]] = defaultdict(
    lambda: {"count": 0, "reset_time": time.time() + 3600}
)

# API key database (production should use PostgreSQL)
# Format: {hashed_key: {"user_id": str, "created_at": datetime, "last_used": datetime, "is_active": bool}}
_api_keys_db: Dict[str, Dict] = {}


class RateLimitConfig:
    """Rate limit configuration per authentication method."""
    API_KEY_LIMIT = 1000  # requests per hour
    JWT_LIMIT = 5000  # requests per hour
    WINDOW_SECONDS = 3600  # 1 hour


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return pwd_context.hash(api_key)


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return pwd_context.verify(api_key, hashed_key)


def create_api_key(user_id: str) -> Tuple[str, str]:
    """
    Create a new API key for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        Tuple of (raw_key, hashed_key) - raw_key shown once, hashed_key stored
    """
    import secrets
    raw_key = f"ak_{secrets.token_urlsafe(32)}"
    hashed_key = hash_api_key(raw_key)
    
    _api_keys_db[hashed_key] = {
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "last_used": None,
        "is_active": True
    }
    
    return raw_key, hashed_key


def revoke_api_key(hashed_key: str) -> bool:
    """
    Revoke an API key.
    
    Args:
        hashed_key: Hashed API key to revoke
        
    Returns:
        True if revoked, False if not found
    """
    if hashed_key in _api_keys_db:
        _api_keys_db[hashed_key]["is_active"] = False
        return True
    return False


async def verify_api_key_from_request(api_key: str) -> Optional[str]:
    """
    Verify API key from request header.
    
    Args:
        api_key: Raw API key from X-API-Key header
        
    Returns:
        user_id if valid, None otherwise
    """
    for hashed_key, data in _api_keys_db.items():
        if data["is_active"] and verify_api_key(api_key, hashed_key):
            # Update last used timestamp
            _api_keys_db[hashed_key]["last_used"] = datetime.utcnow()
            return data["user_id"]
    return None


async def check_rate_limit(identifier: str, limit: int) -> Tuple[bool, Dict[str, int]]:
    """
    Check if request is within rate limit.
    
    Args:
        identifier: Unique identifier (user_id or api_key hash)
        limit: Maximum requests per window
        
    Returns:
        Tuple of (allowed: bool, headers: dict with rate limit info)
    """
    current_time = time.time()
    cache_entry = _rate_limit_cache[identifier]
    
    # Reset window if expired
    if current_time >= cache_entry["reset_time"]:
        cache_entry["count"] = 0
        cache_entry["reset_time"] = current_time + RateLimitConfig.WINDOW_SECONDS
    
    # Check limit
    if cache_entry["count"] >= limit:
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(cache_entry["reset_time"]))
        }
        return False, headers
    
    # Increment count
    cache_entry["count"] += 1
    
    headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(limit - cache_entry["count"]),
        "X-RateLimit-Reset": str(int(cache_entry["reset_time"]))
    }
    
    return True, headers


async def authenticate_request(request: Request) -> Tuple[str, str, Dict[str, str]]:
    """
    Authenticate API request using API key or JWT token.
    
    Supports dual authentication:
    - X-API-Key header: External developers (1000 req/hour)
    - Authorization: Bearer header: Dashboard users (5000 req/hour)
    
    Args:
        request: FastAPI request object
        
    Returns:
        Tuple of (user_id, auth_method, rate_limit_headers)
        
    Raises:
        HTTPException: If authentication fails or rate limit exceeded
    """
    # Try API key authentication first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        user_id = await verify_api_key_from_request(api_key)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key. Get your key at developers.aurelius.ai/keys"
            )
        
        # Check API key rate limit
        allowed, headers = await check_rate_limit(
            f"apikey_{user_id}",
            RateLimitConfig.API_KEY_LIMIT
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {headers['X-RateLimit-Reset']}",
                headers=headers
            )
        
        return user_id, "api_key", headers
    
    # Try JWT token authentication
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        
        # Import JWT verification from existing auth module
        from .auth import verify_token
        token_data = verify_token(token)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired JWT token"
            )
        
        # Check JWT rate limit
        allowed, headers = await check_rate_limit(
            f"jwt_{token_data.user_id}",
            RateLimitConfig.JWT_LIMIT
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {headers['X-RateLimit-Reset']}",
                headers=headers
            )
        
        return token_data.user_id, "jwt", headers
    
    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide X-API-Key header or Authorization: Bearer token"
    )


# Cleanup task for rate limit cache (run periodically)
async def cleanup_rate_limit_cache():
    """Remove expired entries from rate limit cache."""
    while True:
        await asyncio.sleep(3600)  # Run every hour
        current_time = time.time()
        expired_keys = [
            key for key, data in _rate_limit_cache.items()
            if current_time >= data["reset_time"] + 3600  # 1 hour after reset
        ]
        for key in expired_keys:
            del _rate_limit_cache[key]
