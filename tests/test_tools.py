"""Tests for MCP tools via FastMCP (no server startup needed)."""

import pytest
import pytest_asyncio

# These tests will import after server.py is implemented
from src.server import mcp


@pytest.mark.asyncio
async def test_search_api_returns_results():
    async with mcp.test_client() as client:
        result = await client.call_tool("search_api", {"query": "post_note"})
        text = result[0].text
        assert "post_note_edit" in text


@pytest.mark.asyncio
async def test_search_api_with_class_filter():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "search_api", {"query": "setup", "class_name": "Venue"}
        )
        text = result[0].text
        # All results should be from Venue class
        assert "Venue" in text
        assert "OpenReviewClient" not in text


@pytest.mark.asyncio
async def test_get_method_signature_returns_details():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "get_method_signature", {"method_name": "post_note_edit"}
        )
        text = result[0].text
        assert "post_note_edit" in text
        assert "invitation" in text
        assert "signatures" in text
        assert "await_process" in text


@pytest.mark.asyncio
async def test_get_best_practices_returns_section():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "get_best_practices", {"topic": "authentication"}
        )
        text = result[0].text
        assert "token" in text.lower()


@pytest.mark.asyncio
async def test_get_code_example_returns_snippet():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "get_code_example", {"operation": "submit paper"}
        )
        text = result[0].text
        assert "post_note_edit" in text
        assert "```python" in text


@pytest.mark.asyncio
async def test_get_workflow_guide_conference():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "get_workflow_guide", {"workflow_type": "conference"}
        )
        text = result[0].text
        assert "Venue Request" in text or "Deploy" in text


@pytest.mark.asyncio
async def test_get_workflow_guide_journal():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "get_workflow_guide", {"workflow_type": "journal"}
        )
        text = result[0].text
        assert "Submit" in text or "Review" in text
