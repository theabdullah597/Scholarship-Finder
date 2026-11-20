"""Student dashboard privacy and reminder tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.opportunity import Opportunity, OpportunityStatus
from app.models.student import Application, Notification
from app.models.user import StudentProfile, User, UserRole
from app.worker import run_deadline_reminders


async def make_student(db: AsyncSession, email: str) -> User:
    user = User(
        email=email,
        password_hash=hash_password("SuperSecret123!"),
        role=UserRole.STUDENT,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    db.add(StudentProfile(user_id=user.id, timezone="UTC"))
    await db.commit()
    await db.refresh(user)
    return user


def auth_header(user: User) -> dict[str, str]:
    token = create_access_token(subject=str(user.id), role=user.role.value, email=user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_student_data_is_user_scoped(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    first = await make_student(db_session, "first@example.org")
    second = await make_student(db_session, "second@example.org")
    opportunity = Opportunity(
        kind="scholarship",
        title="Published Student Scholarship",
        organization="University",
        description="A published opportunity for testing student data.",
        country="DE",
        fields=["Computer Science"],
        funding_type="fully_funded",
        source_url="https://example.org/student",
        canonical_url="https://example.org/student",
        status=OpportunityStatus.PUBLISHED.value,
        deadline=datetime.now(UTC) + timedelta(days=30),
    )
    db_session.add(opportunity)
    await db_session.commit()

    saved = await client.post(
        "/api/v1/student/applications",
        json={"opportunity_id": str(opportunity.id)},
        headers=auth_header(first),
    )
    assert saved.status_code == 201
    application_id = saved.json()["id"]

    denied = await client.patch(
        f"/api/v1/student/applications/{application_id}",
        json={"status": "submitted"},
        headers=auth_header(second),
    )
    assert denied.status_code == 404

    note = await client.post(
        "/api/v1/student/notes",
        json={"opportunity_id": str(opportunity.id), "content": "My private note"},
        headers=auth_header(first),
    )
    assert note.status_code == 201
    export = await client.get("/api/v1/users/me/export", headers=auth_header(first))
    assert export.status_code == 200
    assert export.json()["notes"][0]["content"] == "My private note"
    assert export.json()["applications"][0]["id"] == application_id

    deleted = await client.delete("/api/v1/users/me", headers=auth_header(first))
    assert deleted.status_code == 204
    refreshed = await client.get("/api/v1/users/me", headers=auth_header(first))
    assert refreshed.status_code == 401


@pytest.mark.asyncio
async def test_deadline_reminders_are_timezone_aware_and_deduplicated(db_session: AsyncSession) -> None:
    user = await make_student(db_session, "reminder@example.org")
    opportunity = Opportunity(
        kind="fellowship",
        title="Reminder Fellowship",
        organization="Research Lab",
        description="A fellowship with a future deadline for reminder testing.",
        country="US",
        fields=["Research"],
        funding_type="partially_funded",
        source_url="https://example.org/reminder",
        canonical_url="https://example.org/reminder",
        status=OpportunityStatus.PUBLISHED.value,
        deadline=datetime(2026, 1, 15, 12, tzinfo=UTC),
    )
    db_session.add(opportunity)
    await db_session.flush()
    db_session.add(Application(user_id=user.id, opportunity_id=opportunity.id))
    await db_session.commit()

    with patch("app.worker.send_deadline_reminder_email", new_callable=AsyncMock) as send_email:
        first_count = await run_deadline_reminders(db_session, datetime(2026, 1, 1, 12, tzinfo=UTC))
        second_count = await run_deadline_reminders(db_session, datetime(2026, 1, 1, 12, tzinfo=UTC))

    notifications = list((await db_session.execute(select(Notification))).scalars().all())
    assert first_count == 1
    assert second_count == 0
    assert len(notifications) == 1
    assert send_email.await_count == 1
