"""Criterion: External fetch audit logging.

Every external context request must create a Supabase context_access_logs row with
source "external_fetch", the session id when known, the query, requested categories,
returned entry ids, and a timestamp -- and the raw (unhashed) token must never appear
in that row.
"""

import asyncio

import httpx

from .conftest import api_url
from .supabase_helpers import fetch_latest_access_log

SKIPTI_AI_PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=30.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_external_fetch_writes_audit_log_row_without_raw_token():
    owner = _login()
    try:
        created = owner.post(
            api_url("/shares"),
            json={
                "label": "tscheck-audit-log",
                "project_id": None,
                "permissions": ["goals"],
                "duration_minutes": 15,
            },
        )
        assert created.status_code == 201, created.text
        share = created.json()
        token = share["connect_url"].rsplit("/", 1)[-1]

        with httpx.Client(timeout=30.0) as anon:
            resp = anon.get(api_url(f"/connect/{token}/context"), params={"q": "tscheck-audit-query-marker"})
            assert resp.status_code == 200, resp.text

        log_row = asyncio.run(fetch_latest_access_log(share["id"]))
        assert log_row is not None, "expected a context_access_logs row for this session"
        assert log_row["source"] == "external_fetch"
        assert str(log_row["session_id"]) == share["id"]
        assert log_row["query"] == "tscheck-audit-query-marker"
        categories = log_row["categories_requested"]
        if isinstance(categories, str):
            import json as _json
            categories = _json.loads(categories)
        assert "Goals" in categories
        entry_ids = log_row["entry_ids_returned"]
        if isinstance(entry_ids, str):
            import json as _json
            entry_ids = _json.loads(entry_ids)
        assert isinstance(entry_ids, list)
        assert log_row["created_at"] is not None
        # The raw bearer token must never be persisted in the log row.
        assert token not in str(log_row)
    finally:
        owner.post(api_url(f"/shares/{share['id']}/revoke"))
        owner.close()
