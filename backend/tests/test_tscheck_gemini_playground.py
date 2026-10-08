"""Criterion: Gemini MCP Playground - real Gemini response with retrieval trace."""

import httpx

from .conftest import api_url

PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def _login() -> httpx.Client:
    c = httpx.Client(timeout=60.0)
    r = c.post(api_url("/auth/demo"))
    assert r.status_code == 200, r.text
    return c


def test_playground_ask_returns_real_answer_and_trace():
    c = _login()
    try:
        resp = c.post(
            api_url("/playground/ask"),
            json={"query": "What is the current status of Skipti AI?", "project_id": PROJECT_ID},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert isinstance(data.get("answer"), str) and len(data["answer"]) > 10

        retrieval = data["retrieval"]
        assert isinstance(retrieval["selected"], list) and len(retrieval["selected"]) > 0
        assert "excluded_count" in retrieval
        assert retrieval["project_revision"] >= 1
    finally:
        c.close()


def test_playground_requires_auth():
    with httpx.Client() as c:
        r = c.post(api_url("/playground/ask"), json={"query": "status", "project_id": PROJECT_ID})
        assert r.status_code == 401, r.text
