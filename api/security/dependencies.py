from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from security.auth import verify_token, TokenData
from typing import Optional

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredentials) -> TokenData:
    """Get the current authenticated user from the JWT token"""
    token = credentials.credentials
    user_data = verify_token(token)
    
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data

def get_token_from_header(auth_header: Optional[str]) -> Optional[str]:
    """Extract JWT token from Authorization header"""
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]
