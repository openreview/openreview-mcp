"""Tests that register_knowledge_tools mounts the knowledge tools onto a FastMCP instance."""

import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import FastMCP

from openreview_mcp import register_knowledge_tools


CORE_TOOLS = {
    "search_api",
    "get_method_signature",
    "search_test_examples",
}

DOCS_TOOLS = {
    "search_docs",
    "gitbook_ai_ask",
}

FAKE_TESTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "fake_tests"
)


class TestRegisterKnowledgeTools:
    def test_registers_core_tools(self):
        mcp = FastMCP("test")
        register_knowledge_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}

        assert CORE_TOOLS.issubset(tool_names), (
            f"Missing tools: {CORE_TOOLS - tool_names}"
        )

    def test_skips_docs_tools_without_gitbook_env(self, monkeypatch):
        monkeypatch.delenv("GITBOOK_API_KEY", raising=False)
        monkeypatch.delenv("GITBOOK_ORG_ID", raising=False)
        monkeypatch.delenv("GITBOOK_SITE_ID", raising=False)
        mcp = FastMCP("test")
        register_knowledge_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}

        assert DOCS_TOOLS.isdisjoint(tool_names), (
            f"Unexpectedly registered docs tools: {DOCS_TOOLS & tool_names}"
        )

    def test_registers_docs_tools_with_gitbook_env(self, monkeypatch):
        monkeypatch.setenv("GITBOOK_API_KEY", "test-key")
        monkeypatch.setenv("GITBOOK_ORG_ID", "test-org")
        monkeypatch.setenv("GITBOOK_SITE_ID", "test-site")
        mcp = FastMCP("test")
        register_knowledge_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}

        assert DOCS_TOOLS.issubset(tool_names), (
            f"Missing docs tools: {DOCS_TOOLS - tool_names}"
        )

    def test_returned_handles_are_callable(self):
        """Each returned handle must be directly callable against real introspection data."""
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp)

        result = handles["search_api"](query="post_note")
        assert "post_note_edit" in result


class TestSearchDocs:
    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        monkeypatch.setenv("GITBOOK_API_KEY", "test-key")
        monkeypatch.setenv("GITBOOK_ORG_ID", "test-org")
        monkeypatch.setenv("GITBOOK_SITE_ID", "test-site")

    def _handles(self):
        mcp = FastMCP("test")
        return register_knowledge_tools(mcp)

    def _mock_response(self, json_data=None, status_code=200, text=None):
        resp = MagicMock()
        resp.status_code = status_code
        if json_data is not None:
            resp.json.return_value = json_data
        if text is not None:
            resp.text = text
        resp.raise_for_status.return_value = None
        return resp

    def test_post_constructs_url_auth_payload(self, monkeypatch):
        posted = {}

        def fake_post(url, headers=None, json=None, **kwargs):
            posted["url"] = url
            posted["headers"] = headers
            posted["json"] = json
            return self._mock_response({"items": []})

        with patch("httpx.Client.post", side_effect=fake_post):
            handles = self._handles()
            out = handles["search_docs"](query="merge profiles")

        assert "test-org" in posted["url"]
        assert "test-site" in posted["url"]
        assert posted["headers"]["Authorization"] == "Bearer test-key"
        assert posted["json"]["query"] == "merge profiles"
        assert posted["json"]["scope"] == {"mode": "default"}
        assert "No matching docs pages found" in out

    def test_page_result_includes_title_path_sections(self):
        data = {
            "items": [
                {
                    "title": "Merge Profiles",
                    "id": "page-id",
                    "score": 0.95,
                    "pages": [
                        {
                            "title": "How to merge profiles",
                            "path": "/profile/merge",
                            "description": "Step-by-step guide",
                            "sections": [{"body": "Contact support"}],
                        }
                    ],
                }
            ]
        }

        with patch("httpx.Client.post", return_value=self._mock_response(data)):
            out = self._handles()["search_docs"](query="merge profiles")

        assert "Merge Profiles" in out
        assert "How to merge profiles" in out
        assert "/profile/merge" in out
        assert "Step-by-step guide" in out
        assert "Contact support" in out

    def test_record_result_includes_url_description(self):
        data = {
            "items": [
                {
                    "type": "record",
                    "title": "API Status",
                    "id": "rec-id",
                    "score": 0.88,
                    "url": "https://status.openreview.net",
                    "description": "System status page",
                }
            ]
        }

        with patch("httpx.Client.post", return_value=self._mock_response(data)):
            out = self._handles()["search_docs"](query="status")

        assert "API Status" in out
        assert "https://status.openreview.net" in out
        assert "System status page" in out

    def test_empty_results_returns_clear_message(self):
        with patch("httpx.Client.post", return_value=self._mock_response({"items": []})):
            out = self._handles()["search_docs"](query="xyz")

        assert "No matching docs pages found" in out

    def test_malformed_response_returns_error_string(self):
        resp = self._mock_response(json_data={"unexpected": "shape"})
        with patch("httpx.Client.post", return_value=resp):
            out = self._handles()["search_docs"](query="foo")

        assert "Found" not in out

    def test_http_error_returns_error_string(self):
        import httpx

        request = httpx.Request("POST", "https://api.gitbook.com/v1/orgs/test-org/sites/test-site/search")
        response = httpx.Response(500, request=request)
        err = httpx.HTTPStatusError("server error", request=request, response=response)
        resp = MagicMock()
        resp.status_code = 500
        resp.raise_for_status.side_effect = err

        with patch("httpx.Client.post", return_value=resp):
            out = self._handles()["search_docs"](query="foo")

        assert "GitBook search returned an error: 500" in out


class TestSearchTestExamplesTool:
    def test_disabled_message_when_no_tests_path(self, tmp_path, monkeypatch):
        """With no env var and a knowledge_path that has no tests/ subdir, the tool returns the disabled string."""
        monkeypatch.delenv("OPENREVIEW_TESTS_PATH", raising=False)
        # Point knowledge at a temp dir with no tests/ subdir.
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp, knowledge_path=str(tmp_path))
        out = handles["search_test_examples"](query="post_decisions")
        assert "Test-suite index unavailable" in out

    def test_returns_results_with_explicit_tests_path(self, monkeypatch):
        monkeypatch.delenv("OPENREVIEW_TESTS_PATH", raising=False)
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp, tests_path=FAKE_TESTS_DIR)
        out = handles["search_test_examples"](query="post_decisions")
        assert "test_post_decisions" in out
        assert "test_clean_conference.py:L" in out

    def test_env_var_resolves_tests_path(self, monkeypatch):
        monkeypatch.setenv("OPENREVIEW_TESTS_PATH", FAKE_TESTS_DIR)
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp)
        out = handles["search_test_examples"](query="post_decisions")
        assert "test_post_decisions" in out

    def test_tests_path_auto_detected_under_knowledge_path(
        self, tmp_path, monkeypatch
    ):
        """If knowledge_path contains a tests/ subdir, the index auto-discovers it."""
        monkeypatch.delenv("OPENREVIEW_TESTS_PATH", raising=False)
        # Set up knowledge_path with only a tests/ subdir.
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        # Copy one fake test file in so the auto-detected index isn't empty.
        src = os.path.join(FAKE_TESTS_DIR, "test_clean_conference.py")
        (tests_dir / "test_clean_conference.py").write_text(
            open(src).read()
        )
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp, knowledge_path=str(tmp_path))
        out = handles["search_test_examples"](query="post_decisions")
        assert "test_post_decisions" in out
