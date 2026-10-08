"""Criterion: Supabase-backed token status.

Unknown token -> 404 "Invalid Skipti session." exactly.
Revoked session -> 410 "The Persona Holder has ended this session." exactly.
Expired session -> 410 "This Skipti session has expired." exactly (expiry forced
deterministically by moving the Supabase row's expires_at into the past, per the
documented spec deviation, instead of waiting out the real TTL).
"""

import httpx

from .conftest import api_url
from .supabase_helpers import force_expire_session

SKIPTI_AI_PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def _create_share(owner: httpx.Client, label: str) -> dict:
    created = owner.post(
        api_url("/shares"),
        json={
            "label": label,
            "project_id": SKIPTI_AI_PROJECT_ID,
            "permissions": ["general_profile"],
            "duration_minutes": 15,
        },
    )
    assert created.status_code == 201, created.text
    return created.json()


def test_unknown_token_returns_404_exact_message():
    with httpx.Client(timeout=30.0) as anon:
        resp = anon.get(api_url("/connect/tscheck-unknown-token-does-not-exist/context"))
        assert resp.status_code == 404, resp.text
        assert resp.text == "Invalid Skipti session.", resp.text


def test_revoked_session_returns_410_exact_message():
    owner = _login()
    try:
        share = _create_share(owner, "tscheck-token-status-revoked")
        token = share["connect_url"].rsplit("/", 1)[-1]
        revoke = owner.post(api_url(f"/shares/{share['id']}/revoke"))
        assert revoke.status_code == 200, revoke.text

        with httpx.Client(timeout=30.0) as anon:
            resp = anon.get(api_url(f"/connect/{token}/context"))
            assert resp.status_code == 410, resp.text
            assert resp.text == "The Persona Holder has ended this session.", resp.text
    finally:
        owner.close()


def test_expired_session_returns_410_exact_message():
    owner = _login()
    try:
        share = _create_share(owner, "tscheck-token-status-expired")
        token = share["connect_url"].rsplit("/", 1)[-1]
        import asyncio

        asyncio.run(force_expire_session(token))

        with httpx.Client(timeout=30.0) as anon:
            resp = anon.get(api_url(f"/connect/{token}/context"))
            assert resp.status_code == 410, resp.text
            assert resp.text == "This Skipti session has expired.", resp.text
    finally:
        owner.post(api_url(f"/shares/{share['id']}/revoke"))
        owner.close()
