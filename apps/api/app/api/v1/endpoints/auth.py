import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.security import (
    create_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.session import get_db
from app.models.user import RefreshToken, StudentProfile, User, UserRole
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.email import send_password_reset_email, send_verification_email

router = APIRouter()

COOKIE_NAME = "refresh_token"
COOKIE_PATH = "/api/v1/auth"


def set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        path=COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path=COOKIE_PATH,
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
    )


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    # Check if email is already taken
    stmt = select(User).where(User.email == data.email.lower())
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    verification_token = generate_secure_token()
    password_hash = hash_password(data.password)

    new_user = User(
        email=data.email.lower(),
        password_hash=password_hash,
        role=UserRole.STUDENT,
        is_verified=False,
        verification_token=verification_token,
    )
    db.add(new_user)
    await db.flush()

    new_profile = StudentProfile(
        user_id=new_user.id,
        full_name=data.full_name,
        target_countries=[],
        fields_of_interest=[],
        timezone="UTC",
    )
    db.add(new_profile)
    await db.commit()

    # Send verification email via Mailpit
    await send_verification_email(new_user.email, verification_token)

    return MessageResponse(message="Registration successful. Please check your email to verify your account.")


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify account email address",
)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    stmt = select(User).where(User.verification_token == data.token)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token.",
        )

    user.is_verified = True
    user.verification_token = None
    await db.commit()

    return MessageResponse(message="Email successfully verified. You may now log in.")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login with JWT and rotating refresh cookie",
)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    stmt = select(User).where(User.email == data.email.lower()).options(selectinload(User.profile))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deleted.",
        )

    if user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended. Please contact support.",
        )

    user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token(
        subject=str(user.id),
        role=user_role_str,
        email=user.email,
    )

    # Create new refresh token family
    raw_refresh_token = generate_secure_token()
    family_id = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    token_record = RefreshToken(
        user_id=user.id,
        family_id=family_id,
        token_hash=hash_token(raw_refresh_token),
        is_revoked=False,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(token_record)
    await db.commit()

    set_refresh_cookie(response, raw_refresh_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Rotate refresh token and issue new access token",
)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> RefreshResponse:
    raw_token = request.cookies.get(COOKIE_NAME)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie missing.",
        )

    token_hash = hash_token(raw_token)
    stmt = (
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .options(selectinload(RefreshToken.user).selectinload(User.profile))
    )
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    if not token_record:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    # Reuse detection: Token has already been used/revoked
    if token_record.is_revoked:
        # Revoke the ENTIRE family immediately
        await db.execute(
            update(RefreshToken).where(RefreshToken.family_id == token_record.family_id).values(is_revoked=True)
        )
        await db.commit()
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected. Session family has been revoked.",
        )

    # Check expiration
    now = datetime.now(UTC)
    if token_record.expires_at.tzinfo is None:
        token_expires_at = token_record.expires_at.replace(tzinfo=UTC)
    else:
        token_expires_at = token_record.expires_at

    if token_expires_at < now:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired.",
        )

    user = token_record.user
    if not user or user.deleted_at is not None or user.is_suspended:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is invalid or suspended.",
        )

    # Rotate token: revoke current, issue new with same family_id
    token_record.is_revoked = True

    new_raw_token = generate_secure_token()
    new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_token_record = RefreshToken(
        user_id=user.id,
        family_id=token_record.family_id,
        token_hash=hash_token(new_raw_token),
        is_revoked=False,
        expires_at=new_expires_at,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.add(new_token_record)
    await db.commit()

    user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    new_access_token = create_access_token(
        subject=str(user.id),
        role=user_role_str,
        email=user.email,
    )

    set_refresh_cookie(response, new_raw_token)

    return RefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out and revoke current refresh token family",
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    raw_token = request.cookies.get(COOKIE_NAME)
    if raw_token:
        token_hash = hash_token(raw_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.execute(stmt)
        token_record = result.scalar_one_or_none()
        if token_record:
            await db.execute(
                update(RefreshToken).where(RefreshToken.family_id == token_record.family_id).values(is_revoked=True)
            )
            await db.commit()

    clear_refresh_cookie(response)
    return MessageResponse(message="Successfully logged out.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request a password reset link",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    stmt = select(User).where(User.email == data.email.lower())
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user and user.deleted_at is None and not user.is_suspended:
        reset_token = generate_secure_token()
        user.reset_password_token = reset_token
        user.reset_password_expires_at = datetime.now(UTC) + timedelta(hours=1)
        await db.commit()
        await send_password_reset_email(user.email, reset_token)

    # Always return 200 OK to prevent email enumeration
    return MessageResponse(message="If that email address is registered, a password reset link has been sent.")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password using a valid reset token",
)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    stmt = select(User).where(User.reset_password_token == data.token)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    now = datetime.now(UTC)
    if not user or not user.reset_password_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    expires_at = (
        user.reset_password_expires_at.replace(tzinfo=UTC)
        if user.reset_password_expires_at.tzinfo is None
        else user.reset_password_expires_at
    )
    if expires_at < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired.",
        )

    user.password_hash = hash_password(data.new_password)
    user.reset_password_token = None
    user.reset_password_expires_at = None

    # Revoke all active sessions for this user on password reset
    await db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(is_revoked=True))
    await db.commit()

    return MessageResponse(message="Password has been successfully reset. Please log in with your new credentials.")
