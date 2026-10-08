"""Criterion: Cookie-less plain-text AI context link.

GET /api/connect/{token}/context must succeed with zero cookies/login, return only
text/plain beginning with "SKIPTI PERSONA CONTEXT", and carry Cache-Control: no-store
plus X-Robots-Tag: noindex.
"""

import httpx

from .conftest import api_url

SKIPTI_AI_PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_cookieless_plaintext_context_link_succeeds_without_auth():
    owner = _login()
    try:
        created = owner.post(
            api_url("/shares"),
            json={
                "label": "tscheck-external-fetch",
                "project_id": SKIPTI_AI_PROJECT_ID,
                "permissions": ["general_profile"],
                "duration_minutes": 15,
            },
        )
        assert created.status_code == 201, created.text
        share = created.json()
        grant_id = share["id"]
        token = share["connect_url"].rsplit("/", 1)[-1]

        # Deliberately brand-new client: no cookies, no Authorization header, no login.
        with httpx.Client(timeout=30.0) as anon:
            resp = anon.get(api_url(f"/connect/{token}/context"))
            assert resp.status_code == 200, resp.text
            content_type = resp.headers.get("content-type", "")
            assert content_type.startswith("text/plain"), content_type
            assert resp.text.startswith("SKIPTI PERSONA CONTEXT"), resp.text[:80]
            assert "no-store" in resp.headers.get("cache-control", "")
            assert "noindex" in resp.headers.get("x-robots-tag", "")
    finally:
        owner.post(api_url(f"/shares/{grant_id}/revoke"))
        owner.close()
