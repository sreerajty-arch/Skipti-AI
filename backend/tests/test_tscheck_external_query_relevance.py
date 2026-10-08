"""Criterion: Query-based relevance filtering.

?q= must use the deterministic existing relevance scoring (shared with the in-app
context router), remove duplicate entries, return only relevant authorized entries,
and plainly state that no relevant approved context was found when nothing matches.
No LLM is invoked for this endpoint -- the response is a synchronous Postgres lookup
plus local scoring, confirmed by code review of services.skipti.rank_external_entries
(pure Python set/scoring, zero calls into services.ai) and exercised here end to end.
"""

import httpx

from .conftest import api_url

SKIPTI_AI_PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_relevant_query_filters_to_matching_category_only():
    owner = _login()
    try:
        created = owner.post(
            api_url("/shares"),
            json={
                "label": "tscheck-relevance-filter",
                "project_id": None,
                "permissions": ["goals", "skills", "ai_preferences"],
                "duration_minutes": 15,
            },
        )
        assert created.status_code == 201, created.text
        share = created.json()
        token = share["connect_url"].rsplit("/", 1)[-1]

        with httpx.Client(timeout=30.0) as anon:
            unfiltered = anon.get(api_url(f"/connect/{token}/context"))
            assert unfiltered.status_code == 200
            assert "## Goals" in unfiltered.text and "## Technical skills" in unfiltered.text

            relevant = anon.get(api_url(f"/connect/{token}/context"), params={"q": "python"})
            assert relevant.status_code == 200, relevant.text
            assert "Python" in relevant.text
            assert "## Goals" not in relevant.text, relevant.text

            irrelevant = anon.get(api_url(f"/connect/{token}/context"), params={"q": "zzqqxx-nonexistent-topic"})
            assert irrelevant.status_code == 200, irrelevant.text
            assert "No relevant approved context was found for this query." in irrelevant.text
    finally:
        owner.post(api_url(f"/shares/{share['id']}/revoke"))
        owner.close()


def test_duplicate_entries_are_deduped_in_query_results():
    owner = _login()
    try:
        dup = owner.post(
            api_url("/persona/entries"),
            json={
                "category": "Goals",
                "label": "tscheck-dup-goal",
                "value": "Build practical AI and machine learning systems",
                "sensitivity": "standard",
            },
        )
        assert dup.status_code == 201, dup.text
        dup_id = dup.json()["id"]

        created = owner.post(
            api_url("/shares"),
            json={"label": "tscheck-relevance-dedupe", "project_id": None, "permissions": ["goals"], "duration_minutes": 15},
        )
        assert created.status_code == 201, created.text
        share = created.json()
        token = share["connect_url"].rsplit("/", 1)[-1]

        with httpx.Client(timeout=30.0) as anon:
            resp = anon.get(api_url(f"/connect/{token}/context"), params={"q": "machine learning"})
            assert resp.status_code == 200, resp.text
            occurrences = resp.text.count("Build practical AI and machine learning systems")
            assert occurrences == 1, resp.text
    finally:
        owner.post(api_url(f"/shares/{share['id']}/revoke"))
        owner.delete(api_url(f"/persona/entries/{dup_id}"))
        owner.close()
