"""Criterion: Category permission isolation.

A Persona Pass shared with only the "goals" permission must return approved active
Goals entries through the external context link and must never expose Hardware,
Tools, or AI preferences content (other unshared categories) anywhere in the body.
"""

import httpx

from .conftest import api_url

SKIPTI_AI_PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_goals_only_pass_excludes_other_categories():
    owner = _login()
    try:
        created = owner.post(
            api_url("/shares"),
            json={
                "label": "tscheck-category-isolation-goals",
                "project_id": None,
                "permissions": ["goals"],
                "duration_minutes": 15,
            },
        )
        assert created.status_code == 201, created.text
        share = created.json()
        token = share["connect_url"].rsplit("/", 1)[-1]

        with httpx.Client(timeout=30.0) as anon:
            resp = anon.get(api_url(f"/connect/{token}/context"))
            assert resp.status_code == 200, resp.text
            body = resp.text

            assert "## Goals" in body, body
            assert "Build practical AI and machine learning systems" in body

            for leaked_category in ("Hardware", "Tools", "AI preferences", "Technical skills"):
                assert f"## {leaked_category}" not in body, body
            assert "Lenovo LOQ" not in body
            assert "VS Code" not in body
            assert "Provide working code first" not in body
    finally:
        owner.post(api_url(f"/shares/{share['id']}/revoke"))
        owner.close()
