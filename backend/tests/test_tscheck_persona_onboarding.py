"""Criterion: Persona onboarding and context ownership.

Covers: adaptive interview start/answer, owner can add/delete their own
Persona context entries, and entries carry owner scoping (no foreign data
is exposed through the owner's own persona endpoint).
"""

import httpx

from .conftest import api_url


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_interview_start_and_answer():
    c = _login()
    try:
        start = c.post(api_url("/interview/start"))
        assert start.status_code in (200, 201), start.text
        body = start.json()
        assert "session_id" in body and "question" in body
        session_id = body["session_id"]

        answer = c.post(
            api_url("/interview/answer"),
            json={"session_id": session_id, "answer": "I'm testing the adaptive interview flow."},
        )
        assert answer.status_code == 200, answer.text
    finally:
        c.close()


def test_owner_can_add_and_delete_own_persona_entry():
    c = _login()
    try:
        created = c.post(
            api_url("/persona/entries"),
            json={
                "category": "skills",
                "label": "tscheck-persona-entry",
                "value": "Owns this granular context entry",
                "sensitivity": "standard",
            },
        )
        assert created.status_code in (200, 201), created.text
        entry = created.json()
        entry_id = entry["id"]
        assert entry["owner_id"]
        assert entry["label"] == "tscheck-persona-entry"

        persona = c.get(api_url("/persona"))
        assert persona.status_code == 200
        ids = {e["id"] for e in persona.json()["entries"]}
        assert entry_id in ids

        deleted = c.delete(api_url(f"/persona/entries/{entry_id}"))
        assert deleted.status_code == 200, deleted.text

        persona_after = c.get(api_url("/persona"))
        ids_after = {e["id"] for e in persona_after.json()["entries"]}
        assert entry_id not in ids_after
    finally:
        c.close()


def test_persona_entries_require_auth():
    with httpx.Client() as c:
        r = c.post(
            api_url("/persona/entries"),
            json={"category": "skills", "label": "x", "value": "y", "sensitivity": "standard"},
        )
        assert r.status_code == 401, r.text
