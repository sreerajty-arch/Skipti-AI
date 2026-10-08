"""Criterion: Project Holder continuity and checkpoints."""

import httpx

from .conftest import api_url

PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_propose_approve_creates_checkpoint_and_rejects_stale_revision():
    c = _login()
    try:
        project = c.get(api_url(f"/projects/{PROJECT_ID}"))
        assert project.status_code == 200, project.text
        current_revision = project.json()["project"]["revision"]

        proposal = c.post(
            api_url(f"/projects/{PROJECT_ID}/proposals"),
            json={
                "update_text": "tscheck: completed the continuity checkpoint test harness.",
                "expected_revision": current_revision,
            },
        )
        assert proposal.status_code in (200, 201), proposal.text
        proposal_id = proposal.json()["id"]
        assert proposal.json()["base_revision"] == current_revision

        # stale approval must be rejected with 409
        stale = c.post(
            api_url(f"/projects/{PROJECT_ID}/proposals/{proposal_id}/approve"),
            json={"expected_revision": current_revision + 999},
        )
        assert stale.status_code == 409, stale.text

        # fresh proposal + correct-revision approval succeeds and advances revision
        current_revision2 = c.get(api_url(f"/projects/{PROJECT_ID}")).json()["project"]["revision"]
        proposal2 = c.post(
            api_url(f"/projects/{PROJECT_ID}/proposals"),
            json={
                "update_text": "tscheck: second continuity checkpoint attempt.",
                "expected_revision": current_revision2,
            },
        )
        assert proposal2.status_code in (200, 201), proposal2.text
        proposal2_id = proposal2.json()["id"]

        approved = c.post(
            api_url(f"/projects/{PROJECT_ID}/proposals/{proposal2_id}/approve"),
            json={"expected_revision": current_revision2},
        )
        assert approved.status_code == 200, approved.text
        checkpoint = approved.json()
        assert checkpoint["revision"] == current_revision2 + 1

        history = c.get(api_url(f"/projects/{PROJECT_ID}/history"))
        assert history.status_code == 200
        revisions = [h["revision"] for h in history.json()]
        assert checkpoint["revision"] in revisions
    finally:
        c.close()


def test_project_endpoints_require_auth():
    with httpx.Client() as c:
        r = c.get(api_url(f"/projects/{PROJECT_ID}"))
        assert r.status_code == 401, r.text
