import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not auth or not auth.credentials:
        raise credentials_exception

    payload = decode_access_token(auth.credentials)
    if not payload:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception from None

    stmt = select(User).where(User.id == user_uuid).options(selectinload(User.profile))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or user.deleted_at is not None:
        raise credentials_exception

    if user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is suspended.",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_role(
    allowed_roles: list[str],
) -> Callable[[User], Coroutine[Any, Any, User]]:
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if user_role_str not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: insufficient role privileges",
            )
        return current_user

    return role_checker
