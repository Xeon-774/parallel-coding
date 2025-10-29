"""Common FastAPI dependencies: DB session, JWT auth, scope checking."""

from __future__ import annotations

from typing import Annotated, Generator

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from orchestrator.core.auth import JWTError, TokenData, check_scope, verify_token
from orchestrator.core.database import get_db as _get_db

security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Expose DB session dependency for API layer.

    Example:
        >>> from fastapi import Depends
        >>> def endpoint(db: Session = Depends(get_db)):
        ...     return 1
    """

    yield from _get_db()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(security)],
) -> TokenData:
    """Validate token and return the current user claims.

    Raises:
        HTTPException: 401 if token invalid or missing.
    """

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authentication credentials")

    try:
        token_data = verify_token(credentials.credentials)
        return token_data
    except JWTError as _exc:  # Intentionally not leaking details
        raise HTTPException(status_code=401, detail="Invalid authentication credentials") from _exc


def require_scope(required_scope: str):
    """Dependency factory for scope checking.

    Returns a function suitable as a dependency that validates the caller has
    the `required_scope` in their token claims.
    """

    def check_scope_dependency(user: Annotated[TokenData, Depends(get_current_user)]) -> TokenData:
        if not check_scope(required_scope, user.scopes):
            raise HTTPException(status_code=403, detail=f"Missing required scope: {required_scope}")
        return user

    return check_scope_dependency
