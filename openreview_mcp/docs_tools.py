"""Tools for searching docs.openreview.net via GitBook."""

import os
from typing import Any

import httpx

DOCS_BASE = "https://docs.openreview.net"
GITBOOK_API_BASE = "https://api.gitbook.com/v1"


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
            body = body[: max(max_len, sources_idx)]
        else:
            body = body[:max_len]
        body = body.rstrip() + "\n\n[Answer truncated due to length]"

    return body
