"""Criterion: Persona Pass QR and revocation."""

import httpx

from .conftest import api_url


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_persona_pass_redeem_replay_and_revocation_lifecycle():
    owner = _login()
    try:
        created = owner.post(
            api_url("/shares"),
            json={
                "label": "tscheck-persona-pass",
                "permissions": ["general_profile", "skills"],
                "duration_minutes": 30,
            },
        )
        assert created.status_code == 201, created.text
        share = created.json()
        grant_id = share["id"]
        connect_url = share["connect_url"]
        token = connect_url.rsplit("/", 1)[-1]
        assert share["status"] == "ready"

        with httpx.Client(timeout=30.0) as guest:
            redeemed = guest.post(api_url("/shares/redeem"), json={"token": token})
            assert redeemed.status_code == 200, redeemed.text
            assert redeemed.json()["status"] == "active"

            # replay must be rejected
            replay = guest.post(api_url("/shares/redeem"), json={"token": token})
            assert replay.status_code == 410, replay.text

            # guest gets only permitted read-only context
            ctx = guest.get(api_url("/guest/context"))
            assert ctx.status_code == 200, ctx.text
            ctx_body = ctx.json()
            assert ctx_body["grant"]["id"] == grant_id
            assert isinstance(ctx_body["persona_entries"], list)

            # owner revokes
            revoke = owner.post(api_url(f"/shares/{grant_id}/revoke"))
            assert revoke.status_code == 200, revoke.text

            # guest's next protected retrieval is rejected
            ctx_after = guest.get(api_url("/guest/context"))
            assert ctx_after.status_code == 401, ctx_after.text
    finally:
        owner.close()


def test_shares_require_auth():
    with httpx.Client() as c:
        r = c.post(
            api_url("/shares"),
            json={"label": "x", "permissions": ["skills"], "duration_minutes": 10},
        )
        assert r.status_code == 401, r.text
