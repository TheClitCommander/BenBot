"""
Authentication and authorization for BensBot trading system.

This module provides JWT-based authentication, user management,
and role-based authorization for the API.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError, validator

logger = logging.getLogger(__name__)

# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"

# JWT Keys (should be stored in secure configuration)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "insecure_default_key_replace_in_production")
JWT_REFRESH_SECRET_KEY = os.environ.get("JWT_REFRESH_SECRET_KEY", "insecure_refresh_key_replace_in_production")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token",
    scopes={
        "admin": "Full access to all endpoints",
        "trader": "Access to trading endpoints",
        "viewer": "Read-only access to data",
    }
)

# Models
class UserRole(BaseModel):
    """User role with permissions."""
    name: str
    description: str
    scopes: List[str]

class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    roles: List[str] = ["viewer"]  # Default role
    hashed_password: str

class UserInDB(User):
    """User model stored in database with additional fields."""
    created_at: str
    last_login: Optional[str] = None

class UserCreate(BaseModel):
    """Model for creating a new user."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: str
    roles: List[str] = ["viewer"]  # Default role

    @validator('password')
    def password_complexity(cls, v):
        """Validate password complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()-_=+[]{}|;:'\",.<>/?`~" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v
    
class UserUpdate(BaseModel):
    """Model for updating user information."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    roles: Optional[List[str]] = None
    password: Optional[str] = None

class UserOut(BaseModel):
    """User model returned to the client."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool
    roles: List[str]
    created_at: str
    last_login: Optional[str] = None

class Token(BaseModel):
    """Token model."""
    access_token: str
    token_type: str
    refresh_token: str
    expires_at: int  # Unix timestamp for token expiration

class TokenData(BaseModel):
    """Data extracted from token."""
    username: str
    scopes: List[str] = []
    exp: int  # Expiration time

# In-memory databases for development (replace with real DB in production)
fake_users_db: Dict[str, UserInDB] = {}
fake_roles_db: Dict[str, UserRole] = {
    "admin": UserRole(
        name="admin",
        description="Administrator with full access",
        scopes=["admin", "trader", "viewer"]
    ),
    "trader": UserRole(
        name="trader",
        description="Trading operator",
        scopes=["trader", "viewer"]
    ),
    "viewer": UserRole(
        name="viewer",
        description="Read-only access",
        scopes=["viewer"]
    )
}

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hashed version."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database."""
    if username in fake_users_db:
        return fake_users_db[username]
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new refresh token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_tokens_for_user(user: UserInDB) -> Token:
    """Create access and refresh tokens for a user."""
    # Get all scopes for the user based on roles
    scopes = set()
    for role in user.roles:
        if role in fake_roles_db:
            scopes.update(fake_roles_db[role].scopes)
    
    # Create token data
    token_data = {
        "sub": user.username,
        "scopes": list(scopes)
    }
    
    # Calculate expiration
    access_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    expires_at = int((datetime.utcnow() + access_expires).timestamp())
    
    # Create both tokens
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_expires
    )
    
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=refresh_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        expires_at=expires_at
    )

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme)
) -> UserInDB:
    """Get the current authenticated user from token."""
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        # Decode token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=token_scopes, exp=payload.get("exp", 0))
    except (jwt.PyJWTError, ValidationError):
        raise credentials_exception
    
    # Check token expiration
    if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": authenticate_value},
        )
    
    # Get user
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    
    # Check if user is disabled
    if user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    
    # Check required scopes
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required scope: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )
    
    return user

async def get_current_active_user(
    current_user: UserInDB = Security(get_current_user, scopes=[])
) -> UserInDB:
    """Get the current active user."""
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user

def create_initial_admin():
    """Create an initial admin user if none exists."""
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    
    if not admin_password:
        logger.warning("No ADMIN_PASSWORD environment variable set, not creating admin user")
        return
    
    if admin_username in fake_users_db:
        logger.info(f"Admin user {admin_username} already exists")
        return
    
    # Create admin user
    fake_users_db[admin_username] = UserInDB(
        username=admin_username,
        email="admin@example.com",
        full_name="System Administrator",
        disabled=False,
        roles=["admin"],
        hashed_password=get_password_hash(admin_password),
        created_at=datetime.utcnow().isoformat()
    )
    
    logger.info(f"Created initial admin user: {admin_username}")

# Create initial admin user on module load
create_initial_admin()

# Router setup
def setup_auth_router(app: FastAPI) -> None:
    """Set up authentication routes."""
    from fastapi import APIRouter, Depends, HTTPException, status
    
    router = APIRouter(prefix="/auth", tags=["auth"])
    
    @router.post("/token", response_model=Token)
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        """OAuth2 compatible token endpoint."""
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login time
        user.last_login = datetime.utcnow().isoformat()
        fake_users_db[user.username] = user
        
        return create_tokens_for_user(user)
    
    @router.post("/refresh", response_model=Token)
    async def refresh_token(refresh_token: str):
        """Endpoint to refresh an access token using a refresh token."""
        try:
            # Decode refresh token
            payload = jwt.decode(refresh_token, JWT_REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check if user exists
            user = get_user(username)
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check if user is disabled
            if user.disabled:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive user",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create new tokens
            return create_tokens_for_user(user)
        
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @router.post("/users", response_model=UserOut)
    async def create_user(
        user_create: UserCreate,
        current_user: UserInDB = Security(get_current_user, scopes=["admin"])
    ):
        """Create a new user (admin only)."""
        # Check if username already exists
        if user_create.username in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if roles are valid
        for role in user_create.roles:
            if role not in fake_roles_db:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}"
                )
        
        # Create user
        hashed_password = get_password_hash(user_create.password)
        user = UserInDB(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            disabled=False,
            roles=user_create.roles,
            hashed_password=hashed_password,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Save user
        fake_users_db[user.username] = user
        
        # Convert to UserOut model for response
        return UserOut(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled,
            roles=user.roles,
            created_at=user.created_at,
            last_login=user.last_login
        )
    
    @router.get("/users/me", response_model=UserOut)
    async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
        """Get current user information."""
        return UserOut(
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            disabled=current_user.disabled,
            roles=current_user.roles,
            created_at=current_user.created_at,
            last_login=current_user.last_login
        )
    
    @router.get("/users", response_model=List[UserOut])
    async def read_users(
        skip: int = 0,
        limit: int = 100,
        current_user: UserInDB = Security(get_current_user, scopes=["admin"])
    ):
        """List all users (admin only)."""
        users = list(fake_users_db.values())[skip : skip + limit]
        return [
            UserOut(
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                disabled=user.disabled,
                roles=user.roles,
                created_at=user.created_at,
                last_login=user.last_login
            )
            for user in users
        ]
    
    @router.put("/users/{username}", response_model=UserOut)
    async def update_user(
        username: str,
        user_update: UserUpdate,
        current_user: UserInDB = Security(get_current_user, scopes=["admin"])
    ):
        """Update user information (admin only)."""
        if username not in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = fake_users_db[username]
        
        # Update fields if provided
        if user_update.email is not None:
            user.email = user_update.email
        
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        
        if user_update.disabled is not None:
            user.disabled = user_update.disabled
        
        if user_update.roles is not None:
            # Check if roles are valid
            for role in user_update.roles:
                if role not in fake_roles_db:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid role: {role}"
                    )
            user.roles = user_update.roles
        
        if user_update.password is not None:
            user.hashed_password = get_password_hash(user_update.password)
        
        # Save user
        fake_users_db[username] = user
        
        # Convert to UserOut model for response
        return UserOut(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled,
            roles=user.roles,
            created_at=user.created_at,
            last_login=user.last_login
        )
    
    @router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_user(
        username: str,
        current_user: UserInDB = Security(get_current_user, scopes=["admin"])
    ):
        """Delete a user (admin only)."""
        if username not in fake_users_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent deleting the current user
        if username == current_user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete yourself"
            )
        
        # Delete user
        del fake_users_db[username]
    
    # Add router to app
    app.include_router(router) 