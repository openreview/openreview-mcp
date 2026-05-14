"""Tests that register_knowledge_tools mounts the knowledge tools onto a FastMCP instance."""

import asyncio
import os

from fastmcp import FastMCP

from openreview_mcp import register_knowledge_tools


EXPECTED_TOOLS = {
    "search_api",
    "get_method_signature",
    "get_best_practices",
    "search_test_examples",
}

FAKE_TESTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "fake_tests"
)


class TestRegisterKnowledgeTools:
    def test_registers_all_tools(self):
        mcp = FastMCP("test")
        register_knowledge_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}

        assert EXPECTED_TOOLS.issubset(tool_names), (
            f"Missing tools: {EXPECTED_TOOLS - tool_names}"
        )

    def test_returns_dict_of_tool_handles(self):
        """register_knowledge_tools returns a dict keyed by tool name for direct test access."""
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp)

        assert isinstance(handles, dict)
        assert set(handles.keys()) == EXPECTED_TOOLS

    def test_returned_handles_are_callable(self):
        """Each returned handle must be directly callable against real introspection data."""
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp)

        result = handles["search_api"](query="post_note")
        assert "post_note_edit" in result

    def test_knowledge_path_override_takes_precedence(self, tmp_path, monkeypatch):
        """An explicit knowledge_path arg must override the env var and bundled default.

        Points at tests/fixtures/ and verifies a tool response contains fixture-only
        content — proving the override is routed through to the knowledge loader.
        """
        # Even with the env var set to a wrong location, the explicit arg wins.
        monkeypatch.setenv("OPENREVIEW_KNOWLEDGE_PATH", str(tmp_path / "wrong"))

        fixtures_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "fixtures"
        )
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp, knowledge_path=fixtures_dir)

        # The fixture best_practices.md has an "Authentication" section mentioning "Token auth"
        result = handles["get_best_practices"](topic="Authentication")
        assert "Token auth" in result


class TestSearchTestExamplesTool:
    def test_disabled_message_when_no_tests_path(self, tmp_path, monkeypatch):
        """With no env var and a knowledge_path that has no tests/ subdir, the tool returns the disabled string."""
        monkeypatch.delenv("OPENREVIEW_TESTS_PATH", raising=False)
        # Point knowledge at a temp dir with no tests/ subdir. The bundled
        # best_practices.md is used as a graceful fallback.
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
        # Set up knowledge_path with only a tests/ subdir — best_practices.md
        # falls back to the bundled copy.
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


class TestBestPracticesFallback:
    def test_falls_back_to_bundled_when_dir_lacks_best_practices(
        self, tmp_path, monkeypatch
    ):
        """A knowledge_path that doesn't contain best_practices.md must not
        error — the bundled copy is used so callers can point the env var at
        an `openreview-py` checkout for the tests-index without supplying a
        best-practices file too.
        """
        monkeypatch.delenv("OPENREVIEW_KNOWLEDGE_PATH", raising=False)
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp, knowledge_path=str(tmp_path))
        # Bundled best_practices.md has an "Authentication" section.
        result = handles["get_best_practices"](topic="Authentication")
        assert "Authentication" in result
