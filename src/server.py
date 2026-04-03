"""FastMCP server for openreview-py with live introspection and static knowledge."""

import logging
import os
from typing import Any

from fastmcp import FastMCP

from src.introspection import introspect_library, search_methods, get_method_details
from src.knowledge import load_knowledge, search_best_practices, search_examples, get_workflow

logger = logging.getLogger("openreview_mcp")

# --- Configuration ---
KNOWLEDGE_PATH = os.environ.get(
    "OPENREVIEW_KNOWLEDGE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "openreview-py"),
)
MCP_HOST = os.environ.get("MCP_HOST", "localhost")
MCP_PORT = int(os.environ.get("MCP_PORT", "4000"))

# --- Startup: build caches ---
logger.info("Introspecting openreview-py library...")
_introspection_cache = introspect_library()
logger.info(
    "Introspected %d classes, %d methods total",
    len(_introspection_cache),
    sum(len(m) for m in _introspection_cache.values()),
)

_llm_txt = os.path.join(KNOWLEDGE_PATH, "llm.txt")
_examples_md = os.path.join(KNOWLEDGE_PATH, "examples.md")
logger.info("Loading knowledge from %s", KNOWLEDGE_PATH)
_knowledge_base = load_knowledge(_llm_txt, _examples_md)
logger.info(
    "Loaded %d practice sections, %d example sections",
    len(_knowledge_base.practices),
    len(_knowledge_base.examples),
)

# --- FastMCP Server ---
mcp = FastMCP(
    name="OpenReview Python Library Expert",
    instructions=(
        "Expert assistant for the openreview-py Python library. "
        "Use these tools to find API methods, best practices, code examples, "
        "and workflow guides for building with OpenReview."
    ),
)


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
    results = search_methods(query, cls_filter, _introspection_cache)
    return _format_search_results(results)


@mcp.tool()
def get_method_signature(method_name: str) -> str:
    """Get full details for a specific openreview-py method.

    Returns complete signature, all parameters with types and defaults,
    and the full docstring.

    Args:
        method_name: Exact or partial method name (e.g., "post_note_edit", "get_all_notes")
    """
    results = get_method_details(method_name, _introspection_cache)
    return _format_method_details(results)


@mcp.tool()
def get_best_practices(topic: str) -> str:
    """Get openreview-py best practices and rules for a topic.

    Returns the relevant section from the best practices guide covering
    authentication, permissions, data model, constraints, anti-patterns, etc.

    Args:
        topic: Topic keyword (e.g., "authentication", "permissions", "content structure", "anti-patterns")
    """
    result = search_best_practices(topic, _knowledge_base)
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
    result = search_examples(operation, _knowledge_base)
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
    result = get_workflow(workflow_type, _knowledge_base)
    if not result:
        return f"No workflow guide found for: {workflow_type}"
    return result


def main() -> None:
    """Start the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
