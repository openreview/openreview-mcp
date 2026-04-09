"""Tests that register_knowledge_tools mounts all 5 knowledge tools onto a FastMCP instance."""

import asyncio
import os

from fastmcp import FastMCP

from openreview_mcp import register_knowledge_tools


class TestRegisterKnowledgeTools:
    def test_registers_five_tools(self):
        mcp = FastMCP("test")
        register_knowledge_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}

        expected = {
            "search_api",
            "get_method_signature",
            "get_best_practices",
            "get_code_example",
            "get_workflow_guide",
        }
        assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"

    def test_returns_dict_of_tool_handles(self):
        """register_knowledge_tools returns a dict keyed by tool name for direct test access."""
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp)

        assert isinstance(handles, dict)
        assert set(handles.keys()) == {
            "search_api",
            "get_method_signature",
            "get_best_practices",
            "get_code_example",
            "get_workflow_guide",
        }

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

        # The fixture llm.txt has an "Authentication" section mentioning "Token auth"
        result = handles["get_best_practices"](topic="Authentication")
        assert "Token auth" in result
