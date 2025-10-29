"""
JWT authentication module for Parallel AI Coding Orchestrator.

Provides secure token generation and validation using JWT (JSON Web Tokens).
Implements password hashing with Argon2id (Excellence AI Standard).

Security:
- Argon2id password hashing (NEVER bcrypt / MD5 / SHA)
- JWT token expiration
- Scope - based authorization
- Secret keys from environment variables

Type Safety:
- Explicit type annotations on all functions
- Pydantic models for token payloads

Usage:
    from orchestrator.core.auth import create_access_token, verify_token

    # Create token
    token = create_access_token(
        user_id="user_123",
        scopes=["supervisor:read", "supervisor:write"]
    )

    # Verify token
    token_data = verify_token(token)
    print(token_data.user_id)  # "user_123"
    print(token_data.scopes)   # ["supervisor:read", "supervisor:write"]
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

# ============================================================================
# Configuration
# ============================================================================

# JWT settings (from environment variables for security)
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "CHANGE_THIS_IN_PRODUCTION_USE_STRONG_SECRET"  # Default for development only
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours default

# Password hashing (Argon2id - Excellence AI Standard)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")  # Argon2id ONLY


# ============================================================================
# Pydantic Models
# ============================================================================


class TokenPayload(BaseModel):
    """
    JWT token payload model.

    Attributes:
        sub: Subject (user ID)
        exp: Expiration timestamp
        scopes: List of permission scopes

    Example:
        >>> payload = TokenPayload(
        ...     sub="user_123",
        ...     exp=datetime.utcnow() + timedelta(hours=24),
        ...     scopes=["supervisor:read"]
        ... )
    """

    sub: str = Field(..., description="User ID")
    exp: datetime = Field(..., description="Expiration time")
    scopes: List[str] = Field(default_factory=list, description="Permission scopes")


class TokenData(BaseModel):
    """
    Validated token data after verification.

    Attributes:
        user_id: User identifier
        scopes: List of permission scopes

    Example:
        >>> token_data = TokenData(
        ...     user_id="user_123",
        ...     scopes=["supervisor:read", "supervisor:write"]
        ... )
    """

    user_id: str
    scopes: List[str] = Field(default_factory=list)


# ============================================================================
# Password Hashing Functions
# ============================================================================


def hash_password(password: str) -> str:
    """
    Hash password using Argon2id.

    Security: Argon2id is the Excellence AI Standard.
    NEVER use bcrypt, MD5, SHA, or any other hashing algorithm.

    Args:
        password: Plain text password

    Returns:
        Hashed password string (Argon2id format)

    Raises:
        ValueError: If password is empty

    Example:
        >>> hashed = hash_password("MySecurePassword123!")
        >>> hashed.startswith("$argon2")  # True
    """
    if not password or not password.strip():
        raise ValueError("Password cannot be empty")

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password (Argon2id format)

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("MyPassword")
        >>> verify_password("MyPassword", hashed)  # True
        >>> verify_password("WrongPassword", hashed)  # False
    """
    if not plain_password or not hashed_password:
        return False

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Invalid hash format or other errors
        return False


# ============================================================================
# JWT Token Functions
# ============================================================================


def create_access_token(
    user_id: str, scopes: List[str], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.

    Args:
        user_id: User identifier (non - empty string)
        scopes: List of permission scopes
        expires_delta: Token expiration duration (default: 24 hours)

    Returns:
        JWT token string

    Raises:
        ValueError: If user_id is empty

    Example:
        >>> token = create_access_token(
        ...     user_id="user_123",
        ...     scopes=["supervisor:read", "supervisor:write"]
        ... )
        >>> len(token) > 100  # JWT tokens are long strings
        True
    """
    if not user_id or not user_id.strip():
        raise ValueError("user_id cannot be empty")

    # Calculate expiration time
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta

    # Create payload with Unix timestamp for exp (JWT standard)
    # Convert UTC datetime to Unix timestamp (seconds since epoch)
    from calendar import timegm

    expire_timestamp = timegm(expire.utctimetuple())

    payload_dict = {"sub": user_id, "exp": expire_timestamp, "scopes": scopes}

    # Encode JWT
    token = jwt.encode(payload_dict, SECRET_KEY, algorithm=ALGORITHM)

    return token


def verify_token(token: str) -> TokenData:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData: Validated token data (user_id, scopes)

    Raises:
        JWTError: If token is invalid, expired, or malformed
        ValueError: If token payload is invalid

    Example:
        >>> token = create_access_token("user_123", ["supervisor:read"])
        >>> data = verify_token(token)
        >>> data.user_id  # "user_123"
        >>> data.scopes   # ["supervisor:read"]
    """
    try:
        # Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract user ID
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise ValueError("Token missing 'sub' claim")

        # Extract scopes
        scopes: List[str] = payload.get("scopes", [])

        return TokenData(user_id=user_id, scopes=scopes)

    except JWTError as e:
        # Token invalid, expired, or malformed
        raise JWTError(f"Token verification failed: {str(e)}")


def check_scope(required_scope: str, token_scopes: List[str]) -> bool:
    """
    Check if required scope is present in token scopes.

    Args:
        required_scope: Required permission scope
        token_scopes: List of scopes from token

    Returns:
        True if required scope is present, False otherwise

    Example:
        >>> scopes = ["supervisor:read", "supervisor:write"]
        >>> check_scope("supervisor:read", scopes)  # True
        >>> check_scope("supervisor:delete", scopes)  # False
    """
    return required_scope in token_scopes


# ============================================================================
# Development Utilities
# ============================================================================


def create_dev_token(user_id: str = "dev_user", scopes: Optional[List[str]] = None) -> str:
    """
    Create development token with full permissions.

    WARNING: Only for development / testing. NEVER use in production.

    Args:
        user_id: Development user ID (default: "dev_user")
        scopes: Permission scopes (default: all scopes)

    Returns:
        JWT token string

    Example:
        >>> dev_token = create_dev_token()
        >>> # Use this token for testing API endpoints
    """
    if scopes is None:
        # Grant all scopes for development
        scopes = [
            "supervisor:read",
            "supervisor:write",
            "resources:read",
            "resources:write",
            "jobs:read",
            "jobs:write",
        ]

    return create_access_token(user_id, scopes, timedelta(days=365))


# ============================================================================
# Example Usage (for documentation)
# ============================================================================

if __name__ == "__main__":
    # This code only runs when executing the module directly
    # (not when importing as a module)

    print("=== Password Hashing Example ===")
    password = "MySecurePassword123!"
    hashed = hash_password(password)
    print(f"Original: {password}")
    print(f"Hashed: {hashed[:50]}...")
    print(f"Verification: {verify_password(password, hashed)}")
    print()

    print("=== JWT Token Example ===")
    token = create_access_token(user_id="user_123", scopes=["supervisor:read", "supervisor:write"])
    print(f"Token: {token[:50]}...")
    print()

    print("=== Token Verification Example ===")
    token_data = verify_token(token)
    print(f"User ID: {token_data.user_id}")
    print(f"Scopes: {token_data.scopes}")
    print()

    print("=== Scope Check Example ===")
    has_read = check_scope("supervisor:read", token_data.scopes)
    has_delete = check_scope("supervisor:delete", token_data.scopes)
    print(f"Has supervisor:read: {has_read}")
    print(f"Has supervisor:delete: {has_delete}")
