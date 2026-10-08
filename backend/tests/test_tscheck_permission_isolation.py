"""Criterion: Permission and project isolation.

A pass without general_profile/hardware access must not return the Hardware entry,
and a Skipti AI pass must not expose Focus Room project content.
"""

import httpx

from .conftest import api_url

SKIPTI_AI_PROJECT_ID = "11111111-1111-4111-8111-111111111111"
FOCUS_ROOM_PROJECT_ID = "22222222-2222-4222-8222-222222222222"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_limited_permissions_exclude_hardware_and_other_project():
    owner = _login()
    try:
        created = owner.post(
            api_url("/shares"),
            json={
                "label": "tscheck-permission-isolation",
                "project_id": SKIPTI_AI_PROJECT_ID,
                "permissions": ["skills"],
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

            ctx = guest.get(api_url("/guest/context"))
            assert ctx.status_code == 200, ctx.text
            body = ctx.json()

            # No Hardware entry (constraint category) should leak without general_profile permission.
            labels = [entry["label"] for entry in body["persona_entries"]]
            categories = [entry["category"] for entry in body["persona_entries"]]
            assert "Primary laptop" not in labels
            assert "Hardware" not in categories

            # Skipti AI pass does not expose Focus Room content anywhere in the payload.
            raw = ctx.text
            assert FOCUS_ROOM_PROJECT_ID not in raw
            assert "Focus Room" not in raw

            # Chat retrieval must never surface the other project's canonical content or the
            # excluded Hardware entry as *retrieved context* (the model may still generically
            # use the term "Focus Room" back to the user since it was asked about by name --
            # what matters is that no actual Focus Room/Hardware data was selected/retrieved).
            chat = guest.post(api_url("/guest/chat"), json={"message": "Tell me about Focus Room and my hardware."})
            assert chat.status_code == 200, chat.text
            chat_body = chat.json()
            selected_ids = [item["id"] for item in chat_body["retrieval"]["selected"]]
            selected_values = [item["value"] for item in chat_body["retrieval"]["selected"]]
            assert not any(FOCUS_ROOM_PROJECT_ID in sid for sid in selected_ids)
            assert "Lenovo LOQ, 16 GB RAM, NVIDIA RTX 3050 6 GB" not in selected_values
            assert "Session reflection flow" not in chat.text
            assert "Keep interaction motion subtle and purposeful" not in chat.text
        finally:
            guest.close()
            owner.post(api_url(f"/shares/{grant_id}/revoke"))
    finally:
        owner.close()
