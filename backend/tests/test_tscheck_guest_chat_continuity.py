"""Criteria: Real permission-aware Gemini chat, Project continuity, and
Bounded multi-turn continuity / session isolation."""

import httpx

from .conftest import api_url

SKIPTI_AI_PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=60.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def _create_and_redeem(owner: httpx.Client, label: str, permissions: list[str], retain: bool = False) -> tuple[str, httpx.Client]:
    created = owner.post(
        api_url("/shares"),
        json={
            "label": label,
            "project_id": SKIPTI_AI_PROJECT_ID,
            "permissions": permissions,
            "duration_minutes": 30,
            "retain_chat_until_expiry": retain,
        },
    )
    assert created.status_code == 201, created.text
    share = created.json()
    token = share["connect_url"].rsplit("/", 1)[-1]
    guest = httpx.Client(timeout=60.0)
    redeemed = guest.post(api_url("/shares/redeem"), json={"token": token})
    assert redeemed.status_code == 200, redeemed.text
    return share["id"], guest


def test_guest_chat_uses_project_progress_with_trace_and_multiturn_isolation():
    owner = _login()
    try:
        grant_id, guest_a = _create_and_redeem(
            owner, "tscheck-chat-continuity-a", ["general_profile", "project_progress"]
        )
        try:
            # Project continuity: ask what to do next without restating progress.
            first = guest_a.post(api_url("/guest/chat"), json={"message": "What should I work on next on this project?"})
            assert first.status_code == 200, first.text
            body = first.json()
            assert body["answer"], "expected a non-empty Gemini answer"
            assert body["retrieval"]["project_revision"] and body["retrieval"]["project_revision"] >= 1
            assert len(body["retrieval"]["selected"]) > 0
            for item in body["retrieval"]["selected"]:
                assert "reason" in item and item["reason"]
            assert "approximate_tokens" in body["retrieval"]
            assert body["message"]["role"] == "assistant"

            # Multi-turn continuity: follow-up references the preceding turn implicitly via history.
            second = guest_a.post(api_url("/guest/chat"), json={"message": "Can you remind me what you just said about blockers?"})
            assert second.status_code == 200, second.text

            # guest/context should now show both turns bounded in recent_messages.
            ctx = guest_a.get(api_url("/guest/context"))
            assert ctx.status_code == 200, ctx.text
            ctx_body = ctx.json()
            assert len(ctx_body["recent_messages"]) >= 4  # 2 user + 2 assistant
            assert ctx_body["project"] is not None
            assert ctx_body["project"]["blockers"] is not None  # project_progress permission grants blockers field

            session_a_contents = {m["content"] for m in ctx_body["recent_messages"]}
        finally:
            pass

        # Session isolation: a second, separately redeemed session must not see session A's messages.
        grant_id_b, guest_b = _create_and_redeem(
            owner, "tscheck-chat-continuity-b", ["general_profile", "project_progress"]
        )
        try:
            ctx_b = guest_b.get(api_url("/guest/context"))
            assert ctx_b.status_code == 200, ctx_b.text
            ctx_b_body = ctx_b.json()
            assert ctx_b_body["recent_messages"] == []
            session_b_before_contents = {m["content"] for m in ctx_b_body["recent_messages"]}
            assert not (session_b_before_contents & session_a_contents)

            third = guest_b.post(api_url("/guest/chat"), json={"message": "What should I work on next?"})
            assert third.status_code == 200, third.text

            ctx_b_after = guest_b.get(api_url("/guest/context"))
            assert ctx_b_after.status_code == 200
            b_contents_after = {m["content"] for m in ctx_b_after.json()["recent_messages"]}
            assert not (b_contents_after & session_a_contents), "session B leaked session A's chat content"
        finally:
            guest_b.close()
            owner.post(api_url(f"/shares/{grant_id_b}/revoke"))
    finally:
        guest_a.close()
        owner.post(api_url(f"/shares/{grant_id}/revoke"))
        owner.close()
