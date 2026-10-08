"""Criterion: Demo owner authentication and dashboard."""

import httpx

from .conftest import api_url


def test_unauthenticated_overview_rejected():
    with httpx.Client() as c:
        r = c.get(api_url("/overview"))
        assert r.status_code == 401, r.text


def test_demo_login_creates_session_and_overview_shows_seed_data():
    with httpx.Client() as c:
        login = c.post(api_url("/auth/demo"))
        assert login.status_code == 200, login.text
        body = login.json()
        assert body["email"] == "demo@skipti.ai"
        assert "skipti_session" in c.cookies or len(c.cookies) > 0

        me = c.get(api_url("/auth/me"))
        assert me.status_code == 200, me.text
        assert me.json()["display_name"] == "Alex Morgan"

        overview = c.get(api_url("/overview"))
        assert overview.status_code == 200, overview.text
        data = overview.json()
        assert data["persona_entries"] >= 6
        assert data["project_count"] >= 2
        project_ids = {p["id"] for p in data["projects"]}
        assert "11111111-1111-4111-8111-111111111111" in project_ids
        assert "22222222-2222-4222-8222-222222222222" in project_ids
