"""Tests for Phase 6 administrative dashboard controls."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.student import Notification
from app.models.user import User, UserRole


async def seed_user(db: AsyncSession, email: str, role: UserRole = UserRole.STUDENT) -> User:
    user = User(
        email=email,
        password_hash=hash_password("SuperSecret123!"),
        role=role,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def headers(user: User) -> dict[str, str]:
    token = create_access_token(subject=str(user.id), role=user.role.value, email=user.email)
    return {"Authorization": f"Bearer {token}"}


async def test_admin_user_management_masks_email_and_audits(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin = await seed_user(db_session, "admin@example.com", UserRole.ADMIN)
    student = await seed_user(db_session, "student@example.com")

    response = await client.get("/api/v1/admin/users", headers=headers(admin))
    assert response.status_code == 200
    data = response.json()
    student_view = next(item for item in data if item["id"] == str(student.id))
    assert student_view["email"] == "st***@example.com"
    assert "password" not in student_view

    response = await client.patch(
        f"/api/v1/admin/users/{student.id}",
        headers=headers(admin),
        json={"is_suspended": True},
    )
    assert response.status_code == 200
    assert response.json()["is_suspended"] is True

    logs = await client.get("/api/v1/admin/audit-logs?action=user.update", headers=headers(admin))
    assert logs.status_code == 200
    assert logs.json()[0]["action"] == "user.update"


async def test_admin_broadcast_targets_active_users(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin = await seed_user(db_session, "admin@example.com", UserRole.ADMIN)
    await seed_user(db_session, "student@example.com")
    suspended = await seed_user(db_session, "suspended@example.com")
    suspended.is_suspended = True
    await db_session.commit()

    response = await client.post(
        "/api/v1/admin/broadcasts",
        headers=headers(admin),
        json={"title": "Maintenance", "message": "Service update", "audience": "student"},
    )
    assert response.status_code == 201
    assert response.json()["recipients"] == 1
    notifications = list((await db_session.execute(select(Notification))).scalars().all())
    assert len(notifications) == 1


async def test_student_cannot_use_admin_dashboard(client: AsyncClient, db_session: AsyncSession) -> None:
    student = await seed_user(db_session, "student@example.com")
    response = await client.get("/api/v1/admin/analytics", headers=headers(student))
    assert response.status_code == 403
