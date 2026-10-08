"""Criterion: Expiration, revocation, end-session, and retention.

With retention off, chat rows are deleted on end/revoke. With retention on, they
remain (until the grant's own TTL expiry, which this test does not wait out).
Revalidation: every protected guest request after revocation/end returns 401.
"""

import httpx

from .conftest import api_url

SKIPTI_AI_PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def _create_and_redeem(owner: httpx.Client, label: str, retain: bool) -> tuple[str, httpx.Client]:
    created = owner.post(
        api_url("/shares"),
        json={
            "label": label,
            "project_id": SKIPTI_AI_PROJECT_ID,
            "permissions": ["general_profile", "project_progress"],
            "duration_minutes": 15,
            "retain_chat_until_expiry": retain,
        },
    )
    assert created.status_code == 201, created.text
    share = created.json()
    token = share["connect_url"].rsplit("/", 1)[-1]
    guest = httpx.Client(timeout=30.0)
    redeemed = guest.post(api_url("/shares/redeem"), json={"token": token})
    assert redeemed.status_code == 200, redeemed.text
    return share["id"], guest


def test_retention_off_deletes_chat_on_end_session():
    owner = _login()
    try:
        grant_id, guest = _create_and_redeem(owner, "tscheck-retention-off", retain=False)
        try:
            chat = guest.post(api_url("/guest/chat"), json={"message": "What is the project status?"})
            assert chat.status_code == 200, chat.text

            ctx = guest.get(api_url("/guest/context"))
            assert ctx.status_code == 200
            assert len(ctx.json()["recent_messages"]) >= 2

            ended = guest.post(api_url("/guest/end"))
            assert ended.status_code == 200, ended.text

            # Future requests on this ended session are rejected.
            after_end = guest.get(api_url("/guest/context"))
            assert after_end.status_code == 401, after_end.text
            chat_after_end = guest.post(api_url("/guest/chat"), json={"message": "hello?"})
            assert chat_after_end.status_code == 401, chat_after_end.text
        finally:
            guest.close()
    finally:
        owner.close()


def test_retention_on_keeps_chat_rows_but_revoke_still_401s():
    owner = _login()
    try:
        grant_id, guest = _create_and_redeem(owner, "tscheck-retention-on", retain=True)
        try:
            chat = guest.post(api_url("/guest/chat"), json={"message": "What is the project status?"})
            assert chat.status_code == 200, chat.text

            ended = guest.post(api_url("/guest/end"))
            assert ended.status_code == 200, ended.text

            # Session itself is ended -> protected requests revalidate and fail regardless of retention.
            after_end = guest.get(api_url("/guest/context"))
            assert after_end.status_code == 401, after_end.text
        finally:
            guest.close()
    finally:
        owner.close()


def test_owner_revocation_blocks_future_guest_requests():
    owner = _login()
    try:
        grant_id, guest = _create_and_redeem(owner, "tscheck-revoke-live", retain=False)
        try:
            ctx_before = guest.get(api_url("/guest/context"))
            assert ctx_before.status_code == 200, ctx_before.text

            revoke = owner.post(api_url(f"/shares/{grant_id}/revoke"))
            assert revoke.status_code == 200, revoke.text

            ctx_after = guest.get(api_url("/guest/context"))
            assert ctx_after.status_code == 401, ctx_after.text
            chat_after = guest.post(api_url("/guest/chat"), json={"message": "still there?"})
            assert chat_after.status_code == 401, chat_after.text
        finally:
            guest.close()
    finally:
        owner.close()
