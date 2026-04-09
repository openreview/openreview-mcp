"""Tests for the 5 MCP knowledge tools via register_knowledge_tools."""

import pytest
from fastmcp import FastMCP

from openreview_mcp import register_knowledge_tools


@pytest.fixture(scope="module")
def tools():
    """Register the knowledge tools onto a fresh FastMCP and return the tool handle dict."""
    mcp = FastMCP("test")
    return register_knowledge_tools(mcp)


def test_search_api_returns_results(tools):
    text = tools["search_api"](query="post_note")
    assert "post_note_edit" in text


def test_search_api_with_class_filter(tools):
    text = tools["search_api"](query="setup", class_name="Venue")
    assert "Venue" in text
    assert "OpenReviewClient" not in text


def test_get_method_signature_returns_details(tools):
    text = tools["get_method_signature"](method_name="post_note_edit")
    assert "post_note_edit" in text
    assert "invitation" in text
    assert "signatures" in text
    assert "await_process" in text


def test_get_best_practices_returns_section(tools):
    text = tools["get_best_practices"](topic="authentication")
    assert "token" in text.lower()


def test_get_code_example_returns_snippet(tools):
    text = tools["get_code_example"](operation="submit paper")
    assert "post_note_edit" in text
    assert "```python" in text


def test_get_workflow_guide_conference(tools):
    text = tools["get_workflow_guide"](workflow_type="conference")
    assert "Venue Request" in text or "Deploy" in text


def test_get_workflow_guide_journal(tools):
    text = tools["get_workflow_guide"](workflow_type="journal")
    assert "Submit" in text or "Review" in text
