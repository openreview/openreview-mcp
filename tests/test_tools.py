"""Tests for the MCP knowledge tools via register_knowledge_tools."""

import os
import re
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pytest
from fastmcp import FastMCP

from openreview_mcp import register_knowledge_tools
from openreview_mcp.docs_tools import gitbook_ai_ask, search_docs


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


class TestSearchDocs:
    """Ranked docs.openreview.net search via GitBook's content search API."""

    def test_returns_results_with_gitbook_api_key(self):
        with patch.dict(
            os.environ,
            {
                "GITBOOK_API_KEY": "test-key",
                "GITBOOK_ORG_ID": "test-org",
                "GITBOOK_SITE_ID": "test-site",
            },
        ):
            with patch("openreview_mcp.docs_tools.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "items": [
                        {
                            "title": "OpenReview",
                            "id": "VorH499wd7ipUjYX5etp",
                            "score": 95.0,
                            "pages": [
                                {
                                    "title": "Expediting Profile Activation",
                                    "path": "getting-started/creating-an-openreview-profile/expediting-profile-activation",
                                    "sections": [
                                        {
                                            "body": "If you received an email with the subject 'OpenReview profile activation pending'..."
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                }
                mock_response.raise_for_status.return_value = None
                mock_client.post.return_value = mock_response
                mock_httpx.Client.return_value.__enter__.return_value = mock_client

                result = search_docs("activate profile")

        assert "Expediting Profile Activation" in result
        assert "score:" in result
        assert "OpenReview profile activation pending" in result

    def test_requires_gitbook_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GITBOOK_API_KEY", None)
            result = search_docs("activate profile")
        assert "GITBOOK_API_KEY is required" in result

    def test_requires_gitbook_ids(self):
        with patch.dict(os.environ, {"GITBOOK_API_KEY": "test-key"}, clear=True):
            result = search_docs("activate profile")
        assert "GITBOOK_ORG_ID and GITBOOK_SITE_ID" in result

    def test_handles_empty_query(self):
        with patch.dict(os.environ, {"GITBOOK_API_KEY": "test-key"}):
            result = search_docs("")
        assert "Provide a query" in result

    def test_no_network_calls_on_empty_query(self):
        with patch.dict(os.environ, {"GITBOOK_API_KEY": "test-key"}):
            with patch("openreview_mcp.docs_tools.httpx") as mock_httpx:
                result = search_docs("")
                assert "Provide a query" in result
                mock_httpx.Client.assert_not_called()


class TestGitbookAiAsk:
    """AI-synthesized docs.openreview.net answer via GitBook's ?ask= endpoint."""

    def test_returns_answer_and_sources(self):
        result = gitbook_ai_ask("how do I add a publication to my profile")
        assert "publication" in result.lower()
        assert "# Sources:" in result
        hosts = {urlparse(url).netloc for url in re.findall(r"https?://[^\s)]+", result)}
        assert "docs.openreview.net" in hosts

    def test_handles_empty_query(self):
        result = gitbook_ai_ask("")
        assert "Provide a query" in result

    def test_no_network_calls_on_empty_query(self):
        with patch("openreview_mcp.docs_tools.httpx") as mock_httpx:
            result = gitbook_ai_ask("")
            assert "Provide a query" in result
            mock_httpx.Client.assert_not_called()
