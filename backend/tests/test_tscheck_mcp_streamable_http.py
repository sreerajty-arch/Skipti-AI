"""Criterion: Real authenticated MCP Streamable HTTP."""

import os

import httpx
import pytest

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
MCP_URL = f"{BACKEND_URL}/mcp/"
MCP_TOKEN = os.environ.get("SKIPTI_MCP_TOKEN", "skipti-demo-mcp-2026")
PROJECT_ID = "11111111-1111-4111-8111-111111111111"


def test_unauthenticated_mcp_initialize_rejected():
    with httpx.Client() as c:
        r = c.post(
            MCP_URL,
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "tscheck-unauth-client", "version": "1.0"},
                },
            },
        )
        assert r.status_code == 401, r.text


@pytest.mark.asyncio
async def test_authenticated_mcp_client_discovers_and_invokes_tools():
    headers = {"Authorization": f"Bearer {MCP_TOKEN}"}
    async with streamablehttp_client(MCP_URL, headers=headers) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = {t.name for t in tools.tools}
            assert "get_project_progress" in tool_names
            assert "search_context" in tool_names

            progress = await session.call_tool(
                "get_project_progress", {"project_id": PROJECT_ID}
            )
            assert progress.content and len(progress.content[0].text) > 0
            assert PROJECT_ID in progress.content[0].text

            search = await session.call_tool("search_context", {"query": "status"})
            assert search.content and "selected" in search.content[0].text
