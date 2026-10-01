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

import httpx
from fastmcp import FastMCP

from openreview_mcp.introspection import (
    get_method_details,
    introspect_library,
    search_methods,
)
from openreview_mcp.tests_index import (
    build_test_index,
    format_test_results,
    search_test_index,
)

logger = logging.getLogger("openreview_mcp")

DOCS_BASE = "https://docs.openreview.net"
GITBOOK_API_BASE = "https://api.gitbook.com/v1"


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


def _get_gitbook_ids() -> tuple[str, str]:
    org = os.environ.get("GITBOOK_ORG_ID", "")
    site = os.environ.get("GITBOOK_SITE_ID", "")
    return org, site


def _format_search_result(item: dict[str, Any]) -> str:
    lines = []
    title = item.get("title", "Untitled")
    item_id = item.get("id", "")
    score = item.get("score")
    lines.append(f"### {title} (score: {score})")
    if item_id:
        lines.append(f"ID: {item_id}")
    if item.get("type") == "record":
        url = item.get("url", "")
        description = (item.get("description") or "").strip()
        if url:
            lines.append(f"URL: {url}")
        if description:
            lines.append(description)
        return "\n".join(lines)
    pages = item.get("pages") or []
    for page in pages[:5]:
        page_title = page.get("title", "Untitled page")
        path = page.get("path", "")
        desc = page.get("description", "").strip()
        lines.append(f"\n**{page_title}**")
        if path:
            lines.append(f"Path: {path}")
        if desc:
            lines.append(desc)
        for section in page.get("sections", [])[:3]:
            body = section.get("body", "").strip()
            if body:
                lines.append(body[:400])
    return "\n".join(lines)


def register_knowledge_tools(
    mcp: FastMCP,
    knowledge_path: str | None = None,
    tests_path: str | None = None,
) -> dict[str, Callable[..., str]]:
    """Register the knowledge tools onto the given FastMCP instance.

    Introspects the installed `openreview-py` at call time — not at import
    time. Optionally builds an index over the upstream openreview-py test
    suite for the `search_test_examples` tool; the tool is registered either
    way and returns a clear disabled message when the index is unavailable.

    Args:
        mcp: The FastMCP server to register tools on.
        knowledge_path: Optional directory hint used to auto-detect the
            openreview-py `tests/` subdir for the test-suite index. Falls
            back to the OPENREVIEW_KNOWLEDGE_PATH env var.
        tests_path: Optional path to an openreview-py `tests/` directory.
            Falls back to OPENREVIEW_TESTS_PATH, then to `{knowledge_path}/tests/`
            when that subdir exists.

    Returns:
        A dict mapping tool name to the registered tool function, primarily
        for direct test access. Production code can ignore the return value.
    """
    logger.info("Introspecting openreview-py library...")
    introspection_cache = introspect_library()
    logger.info(
        "Introspected %d classes, %d methods total",
        len(introspection_cache),
        sum(len(m) for m in introspection_cache.values()),
    )

    # The tests-path auto-detect still uses the original env var / arg as a
    # directory hint, so callers can mount an openreview-py checkout once
    # and get the tests index without setting a second env var.
    knowledge_dir_hint = knowledge_path or os.environ.get(
        "OPENREVIEW_KNOWLEDGE_PATH"
    )
    resolved_tests_path = _resolve_tests_path(tests_path, knowledge_dir_hint)
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

    def _gitbook_configured() -> bool:
        return bool(
            os.environ.get("GITBOOK_API_KEY", "")
            and os.environ.get("GITBOOK_ORG_ID", "")
            and os.environ.get("GITBOOK_SITE_ID", "")
        )

    if _gitbook_configured():

        @mcp.tool()
        def gitbook_ai_ask(query: str) -> str:
            """Ask docs.openreview.net a question and get an AI-synthesized answer.

            Use this when the question is about docs.openreview.net guidance
            (profiles, submissions, reviews, venues, moderation, etc.). It fetches
            the live docs site and returns the top answer with source URLs.

            Args:
                query: Plain-language question or keywords (e.g.
                    'how do I add a publication to my profile',
                    'how to merge profiles',
                    'openreview direct upload license').
            """
            if not query or not query.strip():
                return "Provide a query to ask docs.openreview.net."

            params = {"ask": query.strip()}
            headers = {
                "Accept": "text/markdown, text/plain, */*",
                "User-Agent": "openreview-mcp/1.0",
            }
            try:
                with httpx.Client(timeout=20.0) as client:
                    resp = client.get(DOCS_BASE + "/.md", params=params, headers=headers)
                    resp.raise_for_status()
                    body = resp.text
            except httpx.HTTPStatusError as e:
                return f"docs.openreview.net returned an error: {e.response.status_code}"
            except Exception as e:
                return f"Error fetching docs.openreview.net: {e}"

            if not body or not body.strip():
                return "No answer returned from docs.openreview.net."

            max_len = 8000
            if len(body) > max_len:
                sources_idx = body.rfind("# Sources:")
                if sources_idx > 0:
                    sources = body[sources_idx:]
                    if len(sources) + 2 < max_len:
                        answer_budget = max_len - len(sources) - 2
                        body = body[:answer_budget].rstrip() + "\n\n" + sources
                    else:
                        body = body[:max_len]
                else:
                    body = body[:max_len]
                body = body.rstrip() + "\n\n[Answer truncated due to length]"

            return body

        @mcp.tool()
        def search_docs(query: str) -> str:
            """Search docs.openreview.net and return ranked page/section matches.

            Use this when you want actual docs content rather than a synthesized
            answer. Returns page titles, paths, and section snippets ordered by
            relevance.

            Args:
                query: Keywords or a plain-language question (e.g.
                    'activate profile', 'merge profiles', 'direct upload license').
            """
            if not query or not query.strip():
                return "Provide a query to search docs.openreview.net."

            token = os.environ.get("GITBOOK_API_KEY", "")
            if not token:
                return "GITBOOK_API_KEY is required for docs.openreview.net search."

            org_id, site_id = _get_gitbook_ids()
            if not org_id or not site_id:
                return (
                    "GITBOOK_ORG_ID and GITBOOK_SITE_ID must be set in the environment. "
                    "Get them from your GitBook content API settings or ask the docs admin."
                )

            url = f"{GITBOOK_API_BASE}/orgs/{org_id}/sites/{site_id}/search"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            payload = {"query": query.strip(), "scope": {"mode": "default"}}

            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
            except httpx.HTTPStatusError as e:
                return f"GitBook search returned an error: {e.response.status_code}"
            except Exception as e:
                return f"Error searching docs.openreview.net: {e}"

            items = data.get("items", [])
            if not items:
                return "No matching docs pages found."

            parts = [f"Found {len(items)} result(s) for '{query}':\n"]
            for item in items[:5]:
                parts.append(_format_search_result(item))
                parts.append("")
            return "\n".join(parts).strip()

        logger.info("Registered docs.openreview.net tools (GitBook env vars present)")
    else:
        logger.warning(
            "GitBook env vars not set (GITBOOK_API_KEY, GITBOOK_ORG_ID, GITBOOK_SITE_ID); "
            "skipping docs.openreview.net tool registration"
        )

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

    handles: dict[str, Callable[..., str]] = {
        "search_api": search_api,
        "get_method_signature": get_method_signature,
        "search_test_examples": search_test_examples,
    }
    if _gitbook_configured():
        handles["search_docs"] = search_docs
        handles["gitbook_ai_ask"] = gitbook_ai_ask
    return handles
