"""
Unified dependency for dual authentication support.

Provides a single dependency that accepts either API key or JWT token,
applying appropriate rate limits for each method.
"""
from fastapi import Depends, Request
from typing import Tuple, Dict
from security.api_key_auth import authenticate_request


async def get_authenticated_user(request: Request) -> Tuple[str, str, Dict[str, str]]:
    """
    Dependency for primitives endpoints requiring authentication.
    
    Accepts either:
    - X-API-Key header (external developers, 1000 req/hour)
    - Authorization: Bearer token (dashboard users, 5000 req/hour)
    
    Returns:
        Tuple of (user_id, auth_method, rate_limit_headers)
        
    Raises:
        HTTPException: If authentication fails or rate limit exceeded
        
    Usage:
        @router.post("/some-primitive")
        async def endpoint(auth: Tuple = Depends(get_authenticated_user)):
            user_id, auth_method, headers = auth
            # ... endpoint logic
    """
    return await authenticate_request(request)


# Convenience wrapper for endpoints that just need user_id
async def get_user_id(auth: Tuple = Depends(get_authenticated_user)) -> str:
    """
    Simplified dependency returning only user_id.
    
    Usage:
        @router.post("/some-primitive")
        async def endpoint(user_id: str = Depends(get_user_id)):
            # ... endpoint logic
    """
    user_id, _, _ = auth
    return user_id
