import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import StudentProfile, User, UserRole


# 1. Password Hashing Unit Test
def test_argon2id_password_hashing() -> None:
    raw_pwd = "SuperSecretPassword123!"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert hashed.startswith("$argon2")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


# 2. Registration and Email Verification Flow
@pytest.mark.asyncio
async def test_register_and_verify_flow(client: AsyncClient, db_session: AsyncSession) -> None:
    reg_payload = {
        "email": "student@example.com",
        "password": "Password123!",
        "full_name": "Test Student",
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    assert "Registration successful" in res.json()["message"]

    # Retrieve user from DB to obtain verification token
    stmt = select(User).where(User.email == "student@example.com")
    result = await db_session.execute(stmt)
    user = result.scalar_one()
    assert user.is_verified is False
    assert user.verification_token is not None

    # Verify email
    verify_res = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": user.verification_token},
    )
    assert verify_res.status_code == 200

    await db_session.refresh(user)
    assert user.is_verified is True
    assert user.verification_token is None


# 3. Login Flow & Cookie Issuance
@pytest.mark.asyncio
async def test_login_flow(client: AsyncClient, db_session: AsyncSession) -> None:
    # Seed verified user
    user = User(
        email="login_test@example.com",
        password_hash=hash_password("ValidPassword123!"),
        role=UserRole.STUDENT,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Login with valid credentials
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "login_test@example.com", "password": "ValidPassword123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login_test@example.com"
    assert "refresh_token" in res.cookies

    # Login with invalid password
    bad_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "login_test@example.com", "password": "WrongPassword!"},
    )
    assert bad_res.status_code == 401


# 4. Token Rotation and Reuse Detection
@pytest.mark.asyncio
async def test_token_rotation_and_reuse_revocation(client: AsyncClient, db_session: AsyncSession) -> None:
    # Seed user
    user = User(
        email="rotation_test@example.com",
        password_hash=hash_password("RotatePass123!"),
        role=UserRole.STUDENT,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Initial login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "rotation_test@example.com", "password": "RotatePass123!"},
    )
    assert login_res.status_code == 200
    initial_refresh_cookie = login_res.cookies.get("refresh_token")
    assert initial_refresh_cookie is not None

    # First refresh: Success (Rotation occurs)
    refresh_res_1 = await client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={initial_refresh_cookie}"},
    )
    assert refresh_res_1.status_code == 200
    new_access_token = refresh_res_1.json()["access_token"]
    assert new_access_token is not None
    rotated_refresh_cookie = refresh_res_1.cookies.get("refresh_token")
    assert rotated_refresh_cookie is not None
    assert rotated_refresh_cookie != initial_refresh_cookie

    # REUSE ATTACK: Replay the OLD initial_refresh_cookie
    replay_res = await client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={initial_refresh_cookie}"},
    )
    assert replay_res.status_code == 401
    assert "Token reuse detected" in replay_res.json()["detail"]

    # Verify that the entire family was revoked: Even the new rotated token is now invalid!
    subsequent_res = await client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={rotated_refresh_cookie}"},
    )
    assert subsequent_res.status_code == 401


# 5. Logout
@pytest.mark.asyncio
async def test_logout_clears_cookie_and_revokes(client: AsyncClient, db_session: AsyncSession) -> None:
    user = User(
        email="logout_test@example.com",
        password_hash=hash_password("LogoutPass123!"),
        role=UserRole.STUDENT,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "logout_test@example.com", "password": "LogoutPass123!"},
    )
    cookie_val = login_res.cookies.get("refresh_token")

    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Cookie": f"refresh_token={cookie_val}"},
    )
    assert logout_res.status_code == 200

    # Refresh attempt after logout should fail
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"refresh_token={cookie_val}"},
    )
    assert refresh_res.status_code == 401


# 6. Forgot and Reset Password
@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow(client: AsyncClient, db_session: AsyncSession) -> None:
    user = User(
        email="reset_test@example.com",
        password_hash=hash_password("OldPassword123!"),
        role=UserRole.STUDENT,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()

    forgot_res = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset_test@example.com"},
    )
    assert forgot_res.status_code == 200

    await db_session.refresh(user)
    assert user.reset_password_token is not None

    reset_res = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": user.reset_password_token, "new_password": "BrandNewPassword123!"},
    )
    assert reset_res.status_code == 200

    # Old password fails
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset_test@example.com", "password": "OldPassword123!"},
    )
    assert bad_login.status_code == 401

    # New password succeeds
    good_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset_test@example.com", "password": "BrandNewPassword123!"},
    )
    assert good_login.status_code == 200


# 7. Role-Based Access Control (RBAC): Student vs Admin
@pytest.mark.asyncio
async def test_rbac_student_gets_403_on_admin_route(client: AsyncClient, db_session: AsyncSession) -> None:
    student = User(
        email="student_rbac@example.com",
        password_hash=hash_password("StudentPass123!"),
        role=UserRole.STUDENT,
        is_verified=True,
    )
    admin = User(
        email="admin_rbac@example.com",
        password_hash=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db_session.add_all([student, admin])
    await db_session.commit()

    # Login as student
    student_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "student_rbac@example.com", "password": "StudentPass123!"},
    )
    student_token = student_login.json()["access_token"]

    # Student requests Admin Route -> 403 Forbidden
    student_admin_res = await client.get(
        "/api/v1/admin/test-rbac",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_admin_res.status_code == 403
    assert "insufficient role privileges" in student_admin_res.json()["detail"].lower()

    # Login as admin
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin_rbac@example.com", "password": "AdminPass123!"},
    )
    admin_token = admin_login.json()["access_token"]

    # Admin requests Admin Route -> 200 OK
    admin_res = await client.get(
        "/api/v1/admin/test-rbac",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["message"] == "Admin privileges verified"


# 8. User Profile GET and PATCH /me
@pytest.mark.asyncio
async def test_get_and_patch_me(client: AsyncClient, db_session: AsyncSession) -> None:
    user = User(
        email="profile_test@example.com",
        password_hash=hash_password("ProfilePass123!"),
        role=UserRole.STUDENT,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    profile = StudentProfile(
        user_id=user.id,
        full_name="Original Name",
        citizenship="US",
        target_countries=["DE", "CA"],
        fields_of_interest=["Computer Science"],
        timezone="UTC",
    )
    db_session.add(profile)
    await db_session.commit()

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "profile_test@example.com", "password": "ProfilePass123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # GET /me
    me_res = await client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "profile_test@example.com"
    assert me_data["profile"]["full_name"] == "Original Name"

    # PATCH /me
    patch_res = await client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={
            "full_name": "Updated Name",
            "citizenship": "pk",
            "target_countries": ["us", "gb"],
            "fields_of_interest": ["AI", "BioTech"],
            "target_degree_level": "masters",
            "timezone": "Asia/Karachi",
        },
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["profile"]["full_name"] == "Updated Name"
    assert updated_data["profile"]["citizenship"] == "PK"
    assert updated_data["profile"]["target_countries"] == ["US", "GB"]
    assert updated_data["profile"]["timezone"] == "Asia/Karachi"
