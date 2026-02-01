import uuid
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Security config
SECRET_KEY = "your-secret-key-change-in-production"  # Should be in env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData(BaseModel):
    user_id: str
    email: str
    name: str
    is_admin: bool

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[dict] = None

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: str, email: str, name: str, is_admin: bool = False) -> str:
    """Create a JWT access token"""
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "is_admin": is_admin,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            name=payload.get("name"),
            is_admin=payload.get("is_admin", False),
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def generate_user_id() -> str:
    """Generate a unique user ID"""
    return str(uuid.uuid4())
