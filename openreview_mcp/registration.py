"""Reusable registration of the knowledge tools onto a FastMCP instance.

This module has zero import side effects — no module-level FastMCP is created,
no knowledge is loaded at import time. Downstream consumers can safely
`from openreview_mcp import register_knowledge_tools` and mount the tools
onto their own FastMCP instance.
"""

import logging
import os
from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP

from openreview_mcp.introspection import (
    get_method_details,
    introspect_library,
    search_methods,
)
from openreview_mcp.knowledge import (
    get_workflow,
    load_knowledge,
    search_best_practices,
    search_examples,
)

logger = logging.getLogger("openreview_mcp")

_BUNDLED_KNOWLEDGE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "knowledge_files"
)


def _resolve_knowledge_path(override: str | None = None) -> str:
    """Resolve the knowledge directory: explicit arg > env var > bundled default."""
    if override:
        return override
    env = os.environ.get("OPENREVIEW_KNOWLEDGE_PATH")
    if env:
        return env
    return _BUNDLED_KNOWLEDGE_DIR


def _format_search_results(results: list[dict[str, Any]]) -> str:
    """Format search results as a readable string."""
    if not results:
        return "No results found."
    lines = []
    for r in results:
        doc_line = ""
        if r.get("docstring"):
            first_line = r["docstring"].split("\n")[0].strip()
            doc_line = f" — {first_line}"
        lines.append(f"- {r['class_name']}.{r['name']}{r['signature']}{doc_line}")
    return "\n".join(lines)


def _format_method_details(results: list[dict[str, Any]]) -> str:
    """Format method details as a readable string."""
    if not results:
        return "No methods found matching that name."
    parts = []
    for r in results:
        section = f"### {r['class_name']}.{r['name']}\n\n"
        section += f"**Module:** `{r['module']}`\n"
        section += f"**Signature:** `{r['name']}{r['signature']}`\n\n"
        if r.get("params"):
            section += "**Parameters:**\n"
            for p in r["params"]:
                type_str = f": {p['type']}" if "type" in p else ""
                default_str = f" = {p['default']}" if "default" in p else ""
                section += f"- `{p['name']}{type_str}{default_str}`\n"
            section += "\n"
        if r.get("docstring"):
            section += f"**Docstring:**\n{r['docstring']}\n"
        parts.append(section)
    return "\n---\n\n".join(parts)


def register_knowledge_tools(
    mcp: FastMCP,
    knowledge_path: str | None = None,
) -> dict[str, Callable[..., str]]:
    """Register the 5 knowledge tools onto the given FastMCP instance.

    Reads/introspects the installed `openreview-py` and loads the bundled (or
    override) knowledge files at call time — not at import time.

    Args:
        mcp: The FastMCP server to register tools on.
        knowledge_path: Optional directory containing llm.txt and examples.md.
            Falls back to the OPENREVIEW_KNOWLEDGE_PATH env var, then to the
            knowledge files bundled inside the package.

    Returns:
        A dict mapping tool name to the registered tool function, primarily
        for direct test access. Production code can ignore the return value.
    """
    resolved_path = _resolve_knowledge_path(knowledge_path)

    logger.info("Introspecting openreview-py library...")
    introspection_cache = introspect_library()
    logger.info(
        "Introspected %d classes, %d methods total",
        len(introspection_cache),
        sum(len(m) for m in introspection_cache.values()),
    )

    logger.info("Loading knowledge from %s", resolved_path)
    knowledge_base = load_knowledge(
        os.path.join(resolved_path, "llm.txt"),
        os.path.join(resolved_path, "examples.md"),
    )
    logger.info(
        "Loaded %d practice sections, %d example sections",
        len(knowledge_base.practices),
        len(knowledge_base.examples),
    )

    @mcp.tool()
    def search_api(query: str, class_name: str = "") -> str:
        """Search openreview-py methods and classes by keyword.

        Matches against method names, docstrings, and parameter names.
        Returns up to 15 results sorted by relevance.

        Args:
            query: Search term (e.g., "edge", "post note", "profile merge")
            class_name: Optional filter to a specific class (e.g., "OpenReviewClient", "Venue")
        """
        cls_filter = class_name if class_name else None
        results = search_methods(query, cls_filter, introspection_cache)
        return _format_search_results(results)

    @mcp.tool()
    def get_method_signature(method_name: str) -> str:
        """Get full details for a specific openreview-py method.

        Returns complete signature, all parameters with types and defaults,
        and the full docstring.

        Args:
            method_name: Exact or partial method name (e.g., "post_note_edit", "get_all_notes")
        """
        results = get_method_details(method_name, introspection_cache)
        return _format_method_details(results)

    @mcp.tool()
    def get_best_practices(topic: str) -> str:
        """Get openreview-py best practices and rules for a topic.

        Returns the relevant section from the best practices guide covering
        authentication, permissions, data model, constraints, anti-patterns, etc.

        Args:
            topic: Topic keyword (e.g., "authentication", "permissions", "content structure", "anti-patterns")
        """
        result = search_best_practices(topic, knowledge_base)
        if not result:
            return f"No best practices found for topic: {topic}"
        return result

    @mcp.tool()
    def get_code_example(operation: str) -> str:
        """Get clean, minimal code examples for an openreview-py operation.

        Returns working Python code snippets with realistic placeholders.

        Args:
            operation: What you want to do (e.g., "submit paper", "post edge", "recruit reviewers", "journal decision")
        """
        result = search_examples(operation, knowledge_base)
        if not result:
            return f"No code examples found for: {operation}"
        return result

    @mcp.tool()
    def get_workflow_guide(workflow_type: str) -> str:
        """Get a step-by-step workflow guide with code examples.

        Returns ordered stages for conference or journal workflows,
        or details for a specific stage.

        Args:
            workflow_type: "conference", "journal", or a stage name like "matching", "review", "decision", "submission", "recruitment"
        """
        result = get_workflow(workflow_type, knowledge_base)
        if not result:
            return f"No workflow guide found for: {workflow_type}"
        return result

    return {
        "search_api": search_api,
        "get_method_signature": get_method_signature,
        "get_best_practices": get_best_practices,
        "get_code_example": get_code_example,
        "get_workflow_guide": get_workflow_guide,
    }
