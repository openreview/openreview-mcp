"""Tests that register_knowledge_tools mounts all 5 knowledge tools onto a FastMCP instance."""

import asyncio

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
