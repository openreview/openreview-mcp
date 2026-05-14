"""Tests for the MCP knowledge tools via register_knowledge_tools."""

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


def test_search_api_labels_api_version(tools):
    # get_invitations exists on both clients with different parameter sets;
    # the search output must distinguish them so callers don't copy v1 kwargs
    # onto a v2 call (or vice versa).
    text = tools["search_api"](query="get_invitations")
    assert "[v2] OpenReviewClient.get_invitations" in text
    assert "[v1] Client.get_invitations" in text


def test_get_method_signature_labels_api_version(tools):
    text = tools["get_method_signature"](method_name="get_invitations")
    assert "**API:** v2" in text
    assert "**API:** v1" in text


def test_get_best_practices_returns_section(tools):
    text = tools["get_best_practices"](topic="authentication")
    assert "token" in text.lower()
