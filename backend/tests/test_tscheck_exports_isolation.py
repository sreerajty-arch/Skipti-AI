"""Criterion: Exports and project isolation."""

import httpx

from .conftest import api_url

PROJECT_A = "11111111-1111-4111-8111-111111111111"
PROJECT_B = "22222222-2222-4222-8222-222222222222"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_persona_export_contains_approved_context_and_revision():
    c = _login()
    try:
        resp = c.get(api_url("/persona/export"))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["filename"].endswith(".md")
        assert "Revision" in data["markdown"]
        assert data["revision"] >= 1
        # sensitive entries must never appear unredacted in the export markdown
        assert "sensitive" not in data["markdown"].lower().split("revision")[0]
    finally:
        c.close()


def test_project_retrieval_never_leaks_the_other_seeded_project():
    c = _login()
    try:
        proj_a = c.get(api_url(f"/projects/{PROJECT_A}"))
        proj_b = c.get(api_url(f"/projects/{PROJECT_B}"))
        assert proj_a.status_code == 200, proj_a.text
        assert proj_b.status_code == 200, proj_b.text

        name_a = proj_a.json()["project"]["name"]
        name_b = proj_b.json()["project"]["name"]
        assert name_a != name_b

        raw_a = str(proj_a.json())
        raw_b = str(proj_b.json())
        assert name_b not in raw_a
        assert name_a not in raw_b
        assert PROJECT_B not in raw_a
        assert PROJECT_A not in raw_b
    finally:
        c.close()
