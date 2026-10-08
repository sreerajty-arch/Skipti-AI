"""Criterion: Read-only security, MCP preservation, and mobile UX (API half).

Guest sessions must never be able to create/edit Persona entries or project state;
such attempts are rejected (owner auth required, so an unauthenticated/guest-only
cookie is treated as unauthenticated for these owner-only routes -> 401).
"""

import httpx

from .conftest import api_url

SKIPTI_AI_PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_guest_session_cannot_write_persona_or_project_state():
    owner = _login()
    try:
        created = owner.post(
            api_url("/shares"),
            json={
                "label": "tscheck-readonly-guest",
                "project_id": SKIPTI_AI_PROJECT_ID,
                "permissions": ["general_profile", "project_progress"],
                "duration_minutes": 15,
            },
        )
        assert created.status_code == 201, created.text
        share = created.json()
        grant_id = share["id"]
        token = share["connect_url"].rsplit("/", 1)[-1]

        guest = httpx.Client(timeout=30.0)
        try:
            redeemed = guest.post(api_url("/shares/redeem"), json={"token": token})
            assert redeemed.status_code == 200, redeemed.text

            # Guest's session cookie is a different scheme than the owner cookie; owner-only
            # write routes must reject it outright.
            create_entry = guest.post(
                api_url("/persona/entries"),
                json={"category": "skills", "label": "tscheck-guest-write", "value": "should not be allowed", "sensitivity": "standard"},
            )
            assert create_entry.status_code == 401, create_entry.text

            propose = guest.post(
                api_url(f"/projects/{SKIPTI_AI_PROJECT_ID}/proposals"),
                json={"update_text": "guest tried to update project", "expected_revision": 1, "source_provider": "guest"},
            )
            assert propose.status_code == 401, propose.text

            read_persona = guest.get(api_url("/persona"))
            assert read_persona.status_code == 401, read_persona.text
        finally:
            guest.close()
            owner.post(api_url(f"/shares/{grant_id}/revoke"))
    finally:
        owner.close()


def test_fully_unauthenticated_cannot_write_persona_or_project_state():
    with httpx.Client(timeout=30.0) as anon:
        create_entry = anon.post(
            api_url("/persona/entries"),
            json={"category": "skills", "label": "tscheck-anon-write", "value": "nope", "sensitivity": "standard"},
        )
        assert create_entry.status_code == 401, create_entry.text

        propose = anon.post(
            api_url(f"/projects/{SKIPTI_AI_PROJECT_ID}/proposals"),
            json={"update_text": "anon update", "expected_revision": 1, "source_provider": "anon"},
        )
        assert propose.status_code == 401, propose.text
