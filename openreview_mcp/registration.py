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
    load_knowledge,
    search_best_practices,
)
from openreview_mcp.tests_index import (
    build_test_index,
    format_test_results,
    search_test_index,
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


def _resolve_tests_path(
    override: str | None = None,
    knowledge_path: str | None = None,
) -> str | None:
    """Resolve the openreview-py tests directory.

    Priority: explicit arg > OPENREVIEW_TESTS_PATH env var >
    `{knowledge_path}/tests/` if that subdir exists. Returns None if no
    candidate resolves to an existing directory — the test-suite index is
    optional.
    """
    if override and os.path.isdir(override):
        return override
    env = os.environ.get("OPENREVIEW_TESTS_PATH")
    if env and os.path.isdir(env):
        return env
    if knowledge_path:
        candidate = os.path.join(knowledge_path, "tests")
        if os.path.isdir(candidate):
            return candidate
    return None


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
        api_tag = f"[{r['api_version']}] " if r.get("api_version") else ""
        lines.append(
            f"- {api_tag}{r['class_name']}.{r['name']}{r['signature']}{doc_line}"
        )
    return "\n".join(lines)


def _format_method_details(results: list[dict[str, Any]]) -> str:
    """Format method details as a readable string."""
    if not results:
        return "No methods found matching that name."
    parts = []
    for r in results:
        section = f"### {r['class_name']}.{r['name']}\n\n"
        if r.get("api_version"):
            section += f"**API:** {r['api_version']}\n"
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
    tests_path: str | None = None,
) -> dict[str, Callable[..., str]]:
    """Register the knowledge tools onto the given FastMCP instance.

    Reads/introspects the installed `openreview-py` and loads the bundled (or
    override) knowledge files at call time — not at import time. Optionally
    builds an index over the upstream openreview-py test suite for the
    `search_test_examples` tool; the tool is registered either way and
    returns a clear disabled message when the index is unavailable.

    Args:
        mcp: The FastMCP server to register tools on.
        knowledge_path: Optional directory containing llm.txt.
            Falls back to the OPENREVIEW_KNOWLEDGE_PATH env var, then to the
            bundled knowledge file inside the package.
        tests_path: Optional path to an openreview-py `tests/` directory.
            Falls back to OPENREVIEW_TESTS_PATH, then to `{knowledge_path}/tests/`
            when that subdir exists.

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
    knowledge_base = load_knowledge(os.path.join(resolved_path, "llm.txt"))
    logger.info(
        "Loaded %d practice sections", len(knowledge_base.practices)
    )

    resolved_tests_path = _resolve_tests_path(tests_path, resolved_path)
    test_index = None
    if resolved_tests_path is None:
        logger.info(
            "Test-suite index disabled: set OPENREVIEW_TESTS_PATH or "
            "OPENREVIEW_KNOWLEDGE_PATH=/path/to/openreview-py to enable."
        )
    else:
        try:
            logger.info("Building test-suite index from %s", resolved_tests_path)
            test_index = build_test_index(resolved_tests_path)
            if test_index is not None:
                logger.info(
                    "Indexed %d test functions (helpers methods: %d)",
                    len(test_index.snippets),
                    len(test_index.helpers_methods),
                )
        except Exception as e:  # pragma: no cover — defensive guard
            logger.warning("Failed to build test-suite index: %s", e)
            test_index = None

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
    def search_test_examples(query: str, max_results: int = 5) -> str:
        """Find real usage examples from the openreview-py test suite.

        Returns matching test functions showing how API methods, invitations,
        and full workflow stages are actually called in practice. Tests are the
        canonical, always-current record of intended library usage.

        Requires the openreview-py tests directory to be available. Set
        OPENREVIEW_TESTS_PATH, or point OPENREVIEW_KNOWLEDGE_PATH at a clone
        of the openreview-py repo (the index auto-discovers its `tests/` subdir).

        Args:
            query: Search term (e.g., "post_decisions", "post_note_edit submission", "ethics review")
            max_results: How many test snippets to return (1-10, default 5).
        """
        if test_index is None:
            return (
                "Test-suite index unavailable. Set OPENREVIEW_TESTS_PATH to a "
                "checkout of openreview-py/tests (or OPENREVIEW_KNOWLEDGE_PATH "
                "to the repo root) to enable."
            )
        results = search_test_index(query, test_index, max_results=max_results)
        return format_test_results(
            results, test_index.helpers_methods, test_index.tests_dir
        )

    return {
        "search_api": search_api,
        "get_method_signature": get_method_signature,
        "get_best_practices": get_best_practices,
        "search_test_examples": search_test_examples,
    }
