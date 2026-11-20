"""Comprehensive tests for Phase 3: Ingestion engine, RSS/JSON/HTML fetchers, deduplication, and scheduler."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.ingestion import IngestionRun, IngestionStatus
from app.models.opportunity import Opportunity, Source
from app.models.user import User, UserRole
from app.services.ingestion.engine import IngestionEngine
from app.worker import run_due_sources

SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
 <title>DAAD Scholarships Feed</title>
 <link>https://daad.de</link>
 <description>Global academic scholarships</description>
 <item>
  <title>Helmut Schmidt Master Fellowship in Germany</title>
  <link>https://daad.de/helmut-schmidt-fellowship</link>
  <description><![CDATA[Full scholarship for students in Public Policy in Germany. <script>alert('xss');</script>]]></description>
  <pubDate>Mon, 01 Dec 2026 00:00:00 GMT</pubDate>
  <category>Public Policy</category>
 </item>
 <item>
  <title>Bavarian Research Grant in Munich</title>
  <link>https://daad.de/bavarian-grant</link>
  <description>Research stay in Germany for postdocs.</description>
  <pubDate>Wed, 15 Dec 2026 00:00:00 GMT</pubDate>
  <category>STEM</category>
 </item>
</channel>
</rss>
"""

SAMPLE_JSON_API_DATA = {
    "status": "success",
    "data": {
        "scholarships": [
            {
                "id": 101,
                "title": "Swiss Federal Excellence Fellowship",
                "org": "State Secretariat for Education, Research and Innovation",
                "description": "Fully funded doctoral fellowship in Switzerland with monthly stipend.",
                "url": "https://sbfi.admin.ch/swiss-fellowship?utm_source=feed&utm_medium=partner",
                "country": "CH",
                "disciplines": ["Physics", "Mathematics"],
                "stipend": 2200,
                "currency": "CHF",
                "deadline": "2026-12-15T00:00:00Z",
            },
            {
                "id": 102,
                "title": "Zurich Data Science Research Internship",
                "org": "ETH AI Center",
                "description": "Paid summer internship in Zurich for computer scientists.",
                "url": "https://ai.ethz.ch/summer-internship",
                "country": "CH",
                "disciplines": ["Computer Science", "Artificial Intelligence"],
                "stipend": 3500,
                "currency": "CHF",
                "deadline": "2026-11-20T00:00:00Z",
            },
        ]
    },
}

SAMPLE_HTML_PAGE = """<!DOCTYPE html>
<html>
<body>
  <div class="opportunity-card">
    <h3 class="title"><a href="/fellowships/cern-computing">CERN Summer Student Fellowship in Physics</a></h3>
    <span class="organization">CERN</span>
    <p class="description">Full tuition and living subsidy for students in Geneva, Switzerland.</p>
  </div>
  <div class="opportunity-card">
    <h3 class="title"><a href="https://cern.ch/fellowships/quantum-fellowship">CERN Quantum Computing Research Award</a></h3>
    <span class="organization">CERN Quantum Technology</span>
    <p class="description">Doctoral grant in Switzerland covering high performance computing.</p>
  </div>
</body>
</html>
"""


async def create_admin(db: AsyncSession) -> User:
    user = User(
        email="admin-ingest@opportunity.org",
        password_hash=hash_password("SuperSecret123!"),
        role=UserRole.ADMIN,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_three_sources_ingest(db_session: AsyncSession) -> None:
    """Acceptance: Three sources (RSS, JSON API, HTML) ingest successfully."""
    # 1. Source: RSS
    src_rss = Source(
        name="DAAD RSS Feed",
        source_type="rss",
        url="https://daad.de/feed.xml",
        config={"default_country": "DE", "default_organization": "DAAD"},
    )
    # 2. Source: JSON API
    src_json = Source(
        name="Swiss SBFI API",
        source_type="json_api",
        url="https://sbfi.admin.ch/api/v1/scholarships",
        config={
            "items_path": "data.scholarships",
            "field_mapping": {
                "title": "title",
                "organization": "org",
                "description": "description",
                "url": "url",
                "country": "country",
                "fields": "disciplines",
                "stipend_min": "stipend",
                "stipend_currency": "currency",
                "deadline": "deadline",
            },
        },
    )
    # 3. Source: HTML Scraper
    src_html = Source(
        name="CERN Opportunities Portal",
        source_type="html_scraper",
        url="https://careers.cern/listings",
        config={
            "card_selector": ".opportunity-card",
            "title_selector": "h3.title a",
            "link_selector": "a",
            "desc_selector": "p.description",
            "org_selector": "span.organization",
            "default_country": "CH",
        },
    )
    db_session.add_all([src_rss, src_json, src_html])
    await db_session.commit()

    # Mock HTTP responses for each fetcher
    async def mock_get(url, *args, **kwargs):
        if "feed.xml" in str(url):
            return Response(200, text=SAMPLE_RSS_XML)
        elif "/api/v1/scholarships" in str(url):
            return Response(200, json=SAMPLE_JSON_API_DATA)
        elif "/listings" in str(url):
            return Response(200, text=SAMPLE_HTML_PAGE)
        return Response(404)

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        # Run ingestion for RSS
        run_rss = await IngestionEngine.run_ingestion_for_source(db_session, src_rss)
        assert run_rss.status == IngestionStatus.SUCCESS.value
        assert run_rss.items_found == 2
        assert run_rss.items_created == 2
        assert run_rss.items_failed == 0

        # Run ingestion for JSON API
        run_json = await IngestionEngine.run_ingestion_for_source(db_session, src_json)
        assert run_json.status == IngestionStatus.SUCCESS.value
        assert run_json.items_found == 2
        assert run_json.items_created == 2
        assert run_json.items_failed == 0

        # Run ingestion for HTML Scraper
        run_html = await IngestionEngine.run_ingestion_for_source(db_session, src_html)
        assert run_html.status == IngestionStatus.SUCCESS.value
        assert run_html.items_found == 2
        assert run_html.items_created == 2
        assert run_html.items_failed == 0

    # Total 6 opportunities ingested
    opps = list((await db_session.execute(select(Opportunity))).scalars().all())
    assert len(opps) == 6


@pytest.mark.asyncio
async def test_rerun_creates_no_duplicates(db_session: AsyncSession) -> None:
    """Acceptance: Rerunning ingestion on the same source creates no duplicate opportunities."""
    src = Source(
        name="DAAD RSS Repeat Feed",
        source_type="rss",
        url="https://daad.de/repeat.xml",
        config={"default_country": "DE"},
    )
    db_session.add(src)
    await db_session.commit()

    async def mock_get(url, *args, **kwargs):
        return Response(200, text=SAMPLE_RSS_XML)

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        # First Run: creates 2 items
        run_1 = await IngestionEngine.run_ingestion_for_source(db_session, src)
        assert run_1.items_created == 2
        assert run_1.items_updated == 0

        # Second Run: identical items detected by canonical URL / fuzzy match -> 0 created, 2 updated
        run_2 = await IngestionEngine.run_ingestion_for_source(db_session, src)
        assert run_2.items_created == 0
        assert run_2.items_updated == 2
        assert run_2.items_failed == 0

    # Verify no duplicates in the database
    opps = list((await db_session.execute(select(Opportunity))).scalars().all())
    assert len(opps) == 2


@pytest.mark.asyncio
async def test_item_failures_counted_and_do_not_abort_run(db_session: AsyncSession) -> None:
    """Acceptance: Malformed items are counted in items_failed and do not crash or abort the run."""
    # JSON with 1 valid item and 1 invalid item (missing title and url)
    malformed_json_data = {
        "data": {
            "scholarships": [
                {
                    "title": "Valid Cambridge Research Fellowship",
                    "url": "https://cam.ac.uk/fellowship",
                    "description": "Full study funding in UK.",
                },
                {
                    "title": "",  # invalid: missing title
                    "url": "",  # invalid: missing url
                    "description": "Broken item without links or headers.",
                },
            ]
        }
    }

    src = Source(
        name="Faulty Source",
        source_type="json_api",
        url="https://api.test/faulty",
        config={"items_path": "data.scholarships"},
    )
    db_session.add(src)
    await db_session.commit()

    async def mock_get(url, *args, **kwargs):
        return Response(200, json=malformed_json_data)

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        run = await IngestionEngine.run_ingestion_for_source(db_session, src)
        # Successfully processed valid item, logged failure for invalid item
        assert run.status == IngestionStatus.PARTIAL_FAILURE.value
        assert run.items_found == 2
        assert run.items_created == 1
        assert run.items_failed == 1
        assert "Missing mandatory title or URL" in (run.error_log or "")


@pytest.mark.asyncio
async def test_scheduler_runs_due_sources(db_session: AsyncSession) -> None:
    """Acceptance: Scheduler runs due sources according to fetch_interval_minutes."""
    now = datetime.now(UTC)

    # Source 1: never run before -> due
    src_due_1 = Source(
        name="Due Source 1",
        source_type="rss",
        url="https://due1.org/feed",
        fetch_interval_minutes=60,
        last_run_at=None,
    )
    # Source 2: run 120 minutes ago with interval 60 -> due
    src_due_2 = Source(
        name="Due Source 2",
        source_type="rss",
        url="https://due2.org/feed",
        fetch_interval_minutes=60,
        last_run_at=now - timedelta(minutes=120),
    )
    # Source 3: run 5 minutes ago with interval 60 -> NOT due
    src_not_due = Source(
        name="Not Due Source",
        source_type="rss",
        url="https://notdue.org/feed",
        fetch_interval_minutes=60,
        last_run_at=now - timedelta(minutes=5),
    )
    db_session.add_all([src_due_1, src_due_2, src_not_due])
    await db_session.commit()

    async def mock_get(url, *args, **kwargs):
        return Response(200, text=SAMPLE_RSS_XML)

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        count_run = await run_due_sources(db_session)
        assert count_run == 2

    # Verify run records generated
    runs = list((await db_session.execute(select(IngestionRun))).scalars().all())
    assert len(runs) == 2


@pytest.mark.asyncio
async def test_admin_sources_crud_and_run_now(client: AsyncClient, db_session: AsyncSession) -> None:
    """Acceptance: Admin endpoints for creating, updating, running, and viewing ingestion runs."""
    admin = await create_admin(db_session)
    token = create_access_token(subject=str(admin.id), role=admin.role.value, email=admin.email)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Admin creates source
    res_create = await client.post(
        "/api/v1/admin/sources",
        json={
            "name": "Fulbright US RSS",
            "source_type": "rss",
            "url": "https://fulbright.org/feed.xml",
            "fetch_interval_minutes": 360,
        },
        headers=headers,
    )
    assert res_create.status_code == 201
    source_id = res_create.json()["id"]

    # 2. Admin patches source interval
    res_patch = await client.patch(
        f"/api/v1/admin/sources/{source_id}",
        json={"fetch_interval_minutes": 180},
        headers=headers,
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["fetch_interval_minutes"] == 180

    # 3. Admin triggers run-now
    async def mock_get(url, *args, **kwargs):
        return Response(200, text=SAMPLE_RSS_XML)

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        res_run = await client.post(
            f"/api/v1/admin/sources/{source_id}/run-now",
            headers=headers,
        )
        assert res_run.status_code == 200
        run_data = res_run.json()
        assert run_data["status"] == "success"
        assert run_data["items_created"] == 2

    # 4. Admin views ingestion runs history
    res_history = await client.get("/api/v1/admin/ingestion-runs", headers=headers)
    assert res_history.status_code == 200
    history = res_history.json()
    assert len(history) >= 1
    assert history[0]["source_id"] == source_id

