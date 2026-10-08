"""Criterion: Context Router minimum disclosure."""

import httpx

from .conftest import api_url

PROJECT_ID = "11111111-1111-4111-8111-111111111111"
OTHER_PROJECT_ID = "22222222-2222-4222-8222-222222222222"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_context_search_returns_bounded_selection_with_metadata():
    c = _login()
    try:
        resp = c.post(
            api_url("/context/search"),
            json={"query": "project status and progress", "project_id": PROJECT_ID},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert isinstance(data["selected"], list) and len(data["selected"]) > 0
        assert "available_count" in data
        assert "excluded_count" in data
        assert "approximate_tokens" in data
        assert data["project_revision"] >= 1

        # minimum disclosure: nothing from the unrelated seeded project leaks in
        for item in data["selected"]:
            assert item.get("project_id") in (None, PROJECT_ID)
            assert OTHER_PROJECT_ID not in str(item.get("value", ""))
    finally:
        c.close()


def test_context_search_requires_auth():
    with httpx.Client() as c:
        r = c.post(api_url("/context/search"), json={"query": "status", "project_id": PROJECT_ID})
        assert r.status_code == 401, r.text
