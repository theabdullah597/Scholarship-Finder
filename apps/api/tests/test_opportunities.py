"""Comprehensive tests for Phase 2: Opportunities, filtering, keyset pagination, and admin CRUD."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.opportunity import (
    AuditLog,
    FundingType,
    Opportunity,
    OpportunityKind,
    OpportunityStatus,
)
from app.models.user import User, UserRole

NOW = datetime.now(UTC)


async def create_user(
    db: AsyncSession,
    email: str,
    role: UserRole = UserRole.STUDENT,
) -> User:
    """Helper to seed a verified test user."""
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


async def seed_test_opportunities(db: AsyncSession) -> list[Opportunity]:
    """Helper to seed multiple opportunities for filtering and pagination tests."""
    items = [
        Opportunity(
            kind=OpportunityKind.SCHOLARSHIP.value,
            title="DAAD Master Grant in Engineering",
            organization="DAAD",
            description="Prestigious full master study scholarship in Germany.",
            country="DE",
            fields=["Computer Science", "Engineering"],
            funding_type=FundingType.FULLY_FUNDED.value,
            stipend_amount_min=Decimal("934.00"),
            stipend_amount_max=Decimal("1200.00"),
            stipend_currency="EUR",
            deadline=NOW + timedelta(days=60),
            source_url="https://daad.de/grant",
            canonical_url="https://daad.de/opp-1",
            status=OpportunityStatus.PUBLISHED.value,
        ),
        Opportunity(
            kind=OpportunityKind.INTERNSHIP.value,
            title="CERN Summer Computing Fellowship",
            organization="CERN",
            description="Hands-on computing internship in Geneva, Switzerland.",
            country="CH",
            fields=["Computer Science", "Physics"],
            funding_type=FundingType.FULLY_FUNDED.value,
            stipend_amount_min=Decimal("3400.00"),
            stipend_amount_max=Decimal("3400.00"),
            stipend_currency="CHF",
            deadline=NOW + timedelta(days=20),
            source_url="https://cern.ch/summer",
            canonical_url="https://cern.ch/opp-2",
            status=OpportunityStatus.PUBLISHED.value,
        ),
        Opportunity(
            kind=OpportunityKind.SCHOLARSHIP.value,
            title="Chevening Leadership Award",
            organization="Foreign Commonwealth Office",
            description="Master degree scholarship for future global leaders in the UK.",
            country="GB",
            fields=["Public Health", "Economics"],
            funding_type=FundingType.FULLY_FUNDED.value,
            stipend_amount_min=Decimal("1500.00"),
            stipend_amount_max=Decimal("1800.00"),
            stipend_currency="GBP",
            deadline=NOW + timedelta(days=90),
            source_url="https://chevening.org",
            canonical_url="https://chevening.org/opp-3",
            status=OpportunityStatus.PUBLISHED.value,
        ),
        Opportunity(
            kind=OpportunityKind.GRANT.value,
            title="Mitacs Canadian Mobility Grant",
            organization="Mitacs",
            description="Partial research grant for graduate mobility in Canada.",
            country="CA",
            fields=["Biotechnology"],
            funding_type=FundingType.PARTIALLY_FUNDED.value,
            stipend_amount_min=Decimal("500.00"),
            stipend_amount_max=Decimal("800.00"),
            stipend_currency="CAD",
            deadline=NOW + timedelta(days=120),
            source_url="https://mitacs.ca",
            canonical_url="https://mitacs.ca/opp-4",
            status=OpportunityStatus.PUBLISHED.value,
        ),
        # Expired opportunity
        Opportunity(
            kind=OpportunityKind.SCHOLARSHIP.value,
            title="Expired German Academic Award",
            organization="TUM",
            description="Past year scholarship for historical testing.",
            country="DE",
            fields=["Physics"],
            funding_type=FundingType.FULLY_FUNDED.value,
            stipend_amount_min=Decimal("1000.00"),
            stipend_amount_max=Decimal("1000.00"),
            stipend_currency="EUR",
            deadline=NOW - timedelta(days=30),  # expired
            source_url="https://tum.de/expired",
            canonical_url="https://tum.de/opp-expired",
            status=OpportunityStatus.PUBLISHED.value,
        ),
        # Unpublished opportunities
        Opportunity(
            kind=OpportunityKind.SCHOLARSHIP.value,
            title="Pending Review Scholarship Draft",
            organization="Oxford University",
            description="Awaiting moderation.",
            country="GB",
            fields=["Law"],
            funding_type=FundingType.FULLY_FUNDED.value,
            stipend_amount_min=Decimal("1200.00"),
            stipend_amount_max=Decimal("1500.00"),
            stipend_currency="GBP",
            deadline=NOW + timedelta(days=45),
            source_url="https://ox.ac.uk/draft",
            canonical_url="https://ox.ac.uk/opp-draft",
            status=OpportunityStatus.PENDING_REVIEW.value,
        ),
        Opportunity(
            kind=OpportunityKind.SCHOLARSHIP.value,
            title="Archived Old Award",
            organization="Cambridge",
            description="No longer active.",
            country="GB",
            fields=["Classics"],
            funding_type=FundingType.UNFUNDED.value,
            deadline=NOW + timedelta(days=10),
            source_url="https://cam.ac.uk/archived",
            canonical_url="https://cam.ac.uk/opp-archived",
            status=OpportunityStatus.ARCHIVED.value,
        ),
    ]

    for item in items:
        db.add(item)
    await db.commit()
    return items


@pytest.mark.asyncio
async def test_students_only_see_published_opportunities(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Acceptance: public and students only see published items; unpublished items are hidden."""
    await seed_test_opportunities(db_session)

    res = await client.get("/api/v1/opportunities")
    assert res.status_code == 200
    data = res.json()
    items = data["items"]

    # Only published items returned (4 active published items, expired excluded by default)
    assert len(items) == 4
    for it in items:
        assert it["status"] == "published"
        assert "Pending Review" not in it["title"]
        assert "Archived" not in it["title"]


@pytest.mark.asyncio
async def test_filter_combinations(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Acceptance: filtering by country, kind, funding, field, stipend, and expired works."""
    await seed_test_opportunities(db_session)

    # 1. Filter by country
    res = await client.get("/api/v1/opportunities?country=DE")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["country"] == "DE"
    assert "DAAD" in items[0]["title"]

    # 2. Filter by kind
    res = await client.get("/api/v1/opportunities?kind=internship")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["kind"] == "internship"
    assert "CERN" in items[0]["title"]

    # 3. Filter by field
    res = await client.get("/api/v1/opportunities?field=Computer Science")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 2
    titles = [it["title"] for it in items]
    assert "DAAD Master Grant in Engineering" in titles
    assert "CERN Summer Computing Fellowship" in titles

    # 4. Filter by funding type
    res = await client.get("/api/v1/opportunities?funding=partially_funded")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["funding_type"] == "partially_funded"

    # 5. Filter by stipend range
    res = await client.get("/api/v1/opportunities?stipend_min=3000")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "CERN Summer Computing Fellowship"

    # 6. Filter include_expired=true
    res = await client.get("/api/v1/opportunities?country=DE&include_expired=true")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 2
    titles = [it["title"] for it in items]
    assert "Expired German Academic Award" in titles


@pytest.mark.asyncio
async def test_get_opportunity_by_id_published_vs_unpublished(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Acceptance: Detail endpoint returns published item; returns 404 for draft/unpublished."""
    items = await seed_test_opportunities(db_session)
    pub_opp = [i for i in items if i.status == "published" and "DAAD" in i.title][0]
    draft_opp = [i for i in items if i.status == "pending_review"][0]

    # Published item: 200 OK
    res = await client.get(f"/api/v1/opportunities/{pub_opp.id}")
    assert res.status_code == 200
    assert res.json()["id"] == str(pub_opp.id)
    assert res.json()["title"] == pub_opp.title

    # Draft item: 404 Not Found for public endpoint
    res_draft = await client.get(f"/api/v1/opportunities/{draft_opp.id}")
    assert res_draft.status_code == 404


@pytest.mark.asyncio
async def test_keyset_cursor_stability_when_rows_inserted(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Acceptance: Keyset cursor maintains stable pagination when new rows are inserted concurrently."""
    # Seed 6 opportunities with known created_at ordering
    now = datetime.now(UTC)
    seeded_opps = []
    for i in range(6):
        opp = Opportunity(
            kind=OpportunityKind.SCHOLARSHIP.value,
            title=f"Opportunity {i}",
            organization="Org",
            description="Description for cursor test.",
            country="US",
            fields=["Science"],
            funding_type=FundingType.FULLY_FUNDED.value,
            deadline=now + timedelta(days=30),
            source_url=f"https://example.com/s{i}",
            canonical_url=f"https://example.com/opp-cursor-{i}",
            status=OpportunityStatus.PUBLISHED.value,
            created_at=now - timedelta(minutes=10 * (6 - i)),  # spaced out
        )
        db_session.add(opp)
        seeded_opps.append(opp)
    await db_session.commit()

    # Step 1: Request Page 1 with limit=2
    res_p1 = await client.get("/api/v1/opportunities?limit=2")
    assert res_p1.status_code == 200
    p1_data = res_p1.json()
    assert len(p1_data["items"]) == 2
    cursor_page_1 = p1_data["next_cursor"]
    assert cursor_page_1 is not None

    page_1_ids = [it["id"] for it in p1_data["items"]]

    # Step 2: Insert NEW rows (simulating concurrent ingestion while user reads Page 1)
    new_opp = Opportunity(
        kind=OpportunityKind.SCHOLARSHIP.value,
        title="Concurrent New Arrival Opportunity",
        organization="New Org",
        description="Inserted while paginating.",
        country="US",
        fields=["Science"],
        funding_type=FundingType.FULLY_FUNDED.value,
        deadline=now + timedelta(days=30),
        source_url="https://example.com/concurrent",
        canonical_url="https://example.com/concurrent-1",
        status=OpportunityStatus.PUBLISHED.value,
        created_at=now,  # Brand new timestamp
    )
    db_session.add(new_opp)
    await db_session.commit()

    # Step 3: Fetch Page 2 using cursor
    res_p2 = await client.get(f"/api/v1/opportunities?limit=2&cursor={cursor_page_1}")
    assert res_p2.status_code == 200
    p2_data = res_p2.json()
    assert len(p2_data["items"]) == 2

    page_2_ids = [it["id"] for it in p2_data["items"]]

    # No items from page 1 should bleed into page 2 despite the new insertion!
    for p1_id in page_1_ids:
        assert p1_id not in page_2_ids


@pytest.mark.asyncio
async def test_admin_rbac_protection(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Acceptance: Student accounts receive 403 Forbidden on all /admin/opportunities routes."""
    student = await create_user(db_session, "student@uni.edu", role=UserRole.STUDENT)
    student_token = create_access_token(subject=str(student.id), role=student.role.value, email=student.email)
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Admin list
    res = await client.get("/api/v1/admin/opportunities", headers=student_headers)
    assert res.status_code == 403

    # Admin create
    res = await client.post(
        "/api/v1/admin/opportunities",
        json={
            "kind": "scholarship",
            "title": "Unauthorized Opportunity",
            "organization": "Hack",
            "description": "Will be forbidden.",
            "country": "US",
            "fields": ["CS"],
            "funding_type": "fully_funded",
            "source_url": "https://hack.com",
            "canonical_url": "https://hack.com/canon",
        },
        headers=student_headers,
    )
    assert res.status_code == 403

    # Admin bulk moderate
    res = await client.post(
        "/api/v1/admin/opportunities/bulk-moderate",
        json={"items": [{"id": str(uuid.uuid4()), "action": "publish"}]},
        headers=student_headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_crud_duplicate_detection_and_audit_logging(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Acceptance: Admin can create, patch, verify, archive with duplicate checks and audit logging."""
    admin = await create_user(db_session, "admin@opportunity.org", role=UserRole.ADMIN)
    admin_token = create_access_token(subject=str(admin.id), role=admin.role.value, email=admin.email)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Admin creates opportunity
    create_payload = {
        "kind": "fellowship",
        "title": "Quantum Computing Global Fellowship",
        "organization": "Quantum Alliance",
        "description": "Comprehensive doctoral research fellowship covering tuition and living stipend.",
        "country": "US",
        "fields": ["Quantum Physics", "Computer Science"],
        "funding_type": "fully_funded",
        "stipend_amount_min": 3500.00,
        "stipend_amount_max": 4000.00,
        "stipend_currency": "USD",
        "source_url": "https://quantum.org/apply",
        "canonical_url": "https://quantum.org/fellowship-2026",
    }

    res = await client.post(
        "/api/v1/admin/opportunities",
        json=create_payload,
        headers=admin_headers,
    )
    assert res.status_code == 201
    created_opp = res.json()
    opp_id = created_opp["id"]
    assert created_opp["status"] == "pending_review"

    # 2. Duplicate canonical_url check -> 409 Conflict
    dup_res = await client.post(
        "/api/v1/admin/opportunities",
        json={**create_payload, "title": "Different Title Here"},
        headers=admin_headers,
    )
    assert dup_res.status_code == 409
    assert "canonical URL" in dup_res.json()["detail"]

    # 3. Duplicate title + organization check -> 409 Conflict
    fuzzy_dup_res = await client.post(
        "/api/v1/admin/opportunities",
        json={**create_payload, "canonical_url": "https://different-url.org/other"},
        headers=admin_headers,
    )
    assert fuzzy_dup_res.status_code == 409
    assert "Duplicate opportunity detected" in fuzzy_dup_res.json()["detail"]

    # 4. Admin patches opportunity
    patch_payload = {
        "title": "Updated Quantum Computing Global Fellowship",
        "stipend_amount_max": 4500.00,
    }
    patch_res = await client.patch(
        f"/api/v1/admin/opportunities/{opp_id}",
        json=patch_payload,
        headers=admin_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Quantum Computing Global Fellowship"
    assert float(patch_res.json()["stipend_amount_max"]) == 4500.00

    # 5. Admin verifies (publishes) opportunity
    verify_res = await client.post(
        f"/api/v1/admin/opportunities/{opp_id}/verify",
        headers=admin_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "published"

    # 6. Admin archives opportunity
    archive_res = await client.post(
        f"/api/v1/admin/opportunities/{opp_id}/archive",
        headers=admin_headers,
    )
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == "archived"

    # 7. Check audit logs table for all admin changes
    audit_res = await client.get(
        f"/api/v1/admin/audit-logs?target_id={opp_id}",
        headers=admin_headers,
    )
    assert audit_res.status_code == 200
    audit_logs = audit_res.json()
    actions = [entry["action"] for entry in audit_logs]
    assert "opportunity.create" in actions
    assert "opportunity.patch" in actions
    assert "opportunity.verify" in actions
    assert "opportunity.archive" in actions


@pytest.mark.asyncio
async def test_admin_bulk_moderate_actions(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Acceptance: Admin bulk moderation handles multiple records and creates audit logs."""
    admin = await create_user(db_session, "admin2@opportunity.org", role=UserRole.ADMIN)
    admin_token = create_access_token(subject=str(admin.id), role=admin.role.value, email=admin.email)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create two pending opportunities
    opp1 = Opportunity(
        kind=OpportunityKind.SCHOLARSHIP.value,
        title="Pending Item A",
        organization="Org A",
        description="Description A",
        country="US",
        fields=["Math"],
        funding_type=FundingType.FULLY_FUNDED.value,
        source_url="https://a.org",
        canonical_url="https://a.org/canonical",
        status=OpportunityStatus.PENDING_REVIEW.value,
    )
    opp2 = Opportunity(
        kind=OpportunityKind.SCHOLARSHIP.value,
        title="Pending Item B",
        organization="Org B",
        description="Description B",
        country="US",
        fields=["Math"],
        funding_type=FundingType.FULLY_FUNDED.value,
        source_url="https://b.org",
        canonical_url="https://b.org/canonical",
        status=OpportunityStatus.PENDING_REVIEW.value,
    )
    db_session.add_all([opp1, opp2])
    await db_session.commit()
    await db_session.refresh(opp1)
    await db_session.refresh(opp2)

    # Bulk moderate: approve opp1, reject opp2
    bulk_res = await client.post(
        "/api/v1/admin/opportunities/bulk-moderate",
        json={
            "items": [
                {"id": str(opp1.id), "action": "approve"},
                {"id": str(opp2.id), "action": "reject"},
            ]
        },
        headers=admin_headers,
    )
    assert bulk_res.status_code == 200
    data = bulk_res.json()
    assert data["processed"] == 2
    assert all(r["success"] is True for r in data["results"])

    # Verify updated statuses in database
    await db_session.refresh(opp1)
    await db_session.refresh(opp2)
    assert opp1.status == "published"
    assert opp2.status == "rejected"

    # Verify audit logs created
    audit_stmt = select(AuditLog).where(AuditLog.target_id.in_([str(opp1.id), str(opp2.id)]))
    audit_rows = list((await db_session.execute(audit_stmt)).scalars().all())
    assert len(audit_rows) == 2
