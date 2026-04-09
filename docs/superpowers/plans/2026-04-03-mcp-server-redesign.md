# OpenReview MCP Server Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing 11-tool MCP server with 5 focused tools powered by live introspection of openreview-py and static knowledge files (llm.txt, examples.md).

**Architecture:** Two knowledge layers — live introspection via Python's `inspect` module on the installed openreview-py package, and a static knowledge layer that parses llm.txt and examples.md into indexed sections. FastMCP server exposes 5 tools: `search_api`, `get_method_signature`, `get_best_practices`, `get_code_example`, `get_workflow_guide`.

**Tech Stack:** Python 3.11+, FastMCP, openreview-py, pytest

**Working directories:**
- MCP server: `/Users/cmondragonch/Documents/openreview-mcp`
- openreview-py (knowledge files): `/Users/cmondragonch/Documents/openreview-py`

---

## File Structure

```
openreview-mcp/
├── src/
│   ├── __init__.py          # existing, keep
│   ├── server.py            # REWRITE: FastMCP server + 5 tools
│   ├── introspection.py     # CREATE: live introspection of openreview-py
│   └── knowledge.py         # CREATE: parse llm.txt + examples.md
├── tests/
│   ├── __init__.py          # CREATE
│   ├── conftest.py          # CREATE: shared fixtures
│   ├── fixtures/
│   │   ├── llm.txt          # CREATE: minimal test fixture
│   │   └── examples.md      # CREATE: minimal test fixture
│   ├── test_introspection.py # CREATE: Layer 1 tests
│   ├── test_knowledge.py    # CREATE: Layer 2 tests
│   └── test_tools.py        # CREATE: Layer 3 tests
├── src/introspect.py        # DELETE (replaced by introspection.py)
├── pyproject.toml           # MODIFY: add pytest-asyncio
├── CLAUDE.md                # MODIFY: update structure docs
└── README.md                # MODIFY: update tool docs
```

---

### Task 1: Project scaffolding and test fixtures

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/llm.txt`
- Create: `tests/fixtures/examples.md`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add pytest-asyncio to dev dependencies**

In `pyproject.toml`, add `pytest-asyncio` to the dev dependencies:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.23.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
```

- [ ] **Step 2: Create tests directory and __init__.py**

```bash
mkdir -p tests/fixtures
touch tests/__init__.py
```

- [ ] **Step 3: Create test fixtures — minimal llm.txt**

Create `tests/fixtures/llm.txt`:

```markdown
# openreview-py

> Python client for the OpenReview academic peer review platform.

## Authentication

- Username/password: `OpenReviewClient(username='...', password='...')`
- Token auth: `OpenReviewClient(token='...')` — takes precedence over username/password
- Environment variables: `OPENREVIEW_USERNAME`, `OPENREVIEW_PASSWORD`
- Expired tokens raise `TokenExpiredError`.

## Content Structure

v2 content uses `{'field_name': {'value': actual_data}}` consistently:
- Access: `note.content['title']['value']`
- Never access `note.content['title']` directly — always go through `['value']`

## Conference Workflow

Standard conference stages in order:

1. Venue Request: Post a request form to `openreview.net/Support/-/Request_Form`.
2. Deploy: Post deploy note. Creates venue group, committee groups, and submission invitation.
3. Recruit Committee: Invite SACs, then ACs, then Reviewers.
4. Submission: Authors post papers via `{VenueID}/-/Submission`.
5. Review: Reviewers submit official reviews.
6. Decision: PCs post accept/reject decisions.

## Anti-Patterns to Avoid

- Missing `await_process=True` after edits that trigger process functions.
- Using `get_notes()` when expecting more than 1000 results — use `get_all_notes()`.
- Accessing `note.content['field']` without `['value']`.
```

- [ ] **Step 4: Create test fixtures — minimal examples.md**

Create `tests/fixtures/examples.md`:

````markdown
# openreview-py Code Examples

## Authentication

### Connect to production

```python
import openreview

client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    username='user@example.com',
    password='your_password'
)
```

### Token-based auth

```python
client = openreview.api.OpenReviewClient(
    baseurl='https://api2.openreview.net',
    token='your_bearer_token'
)
```

## Notes

### Submit a paper

```python
from openreview.api import Note

result = client.post_note_edit(
    invitation='VenueID/-/Submission',
    signatures=['~Author_Name1'],
    note=Note(
        content={
            'title': {'value': 'My Paper Title'},
            'abstract': {'value': 'This paper presents...'},
            'authors': {'value': ['Alice Smith']},
            'authorids': {'value': ['~Alice_Smith1']}
        }
    ),
    await_process=True
)
```

## Conference Workflow

### Create venue via request form

```python
request_form = client.post_note(openreview.Note(
    invitation='openreview.net/Support/-/Request_Form',
    signatures=['~PC_Name1'],
    readers=['openreview.net/Support', '~PC_Name1'],
    writers=[],
    content={
        'title': 'Conference 2025',
        'Official Venue Name': 'Conference 2025',
        'Abbreviated Venue Name': 'Conf25'
    }
))
```

### Post a review

```python
from openreview.api import Note

reviewer_client.post_note_edit(
    invitation='Conf25/Submission1/-/Official_Review',
    signatures=['Conf25/Submission1/Reviewer_abc123'],
    note=Note(
        content={
            'review': {'value': 'This paper presents a novel approach...'},
            'rating': {'value': 8},
            'confidence': {'value': 4}
        }
    ),
    await_process=True
)
```
````

- [ ] **Step 5: Create conftest.py with shared fixtures**

Create `tests/conftest.py`:

```python
import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def llm_txt_path():
    return os.path.join(FIXTURES_DIR, "llm.txt")


@pytest.fixture
def examples_md_path():
    return os.path.join(FIXTURES_DIR, "examples.md")
```

- [ ] **Step 6: Install dev dependencies**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && uv pip install -e ".[dev]"`

- [ ] **Step 7: Verify pytest runs (no tests yet)**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && python -m pytest tests/ -v`
Expected: "no tests ran" or "collected 0 items"

- [ ] **Step 8: Commit**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git add tests/ pyproject.toml
git commit -m "chore: add test scaffolding, fixtures, and pytest-asyncio"
```

---

### Task 2: Write Layer 1 tests — introspection

**Files:**
- Create: `tests/test_introspection.py`

- [ ] **Step 1: Write all introspection tests**

Create `tests/test_introspection.py`:

```python
"""Tests for live introspection of the openreview-py library."""

import pytest
from src.introspection import introspect_library, search_methods, get_method_details


@pytest.fixture(scope="module")
def cache():
    return introspect_library()


class TestIntrospectLibrary:
    def test_returns_all_target_classes(self, cache):
        expected_classes = [
            "OpenReviewClient",
            "Client",
            "Note",
            "Invitation",
            "Edge",
            "Group",
            "Tag",
            "Edit",
            "Profile",
            "Venue",
        ]
        for cls_name in expected_classes:
            assert cls_name in cache, f"Missing class: {cls_name}"

    def test_captures_method_signatures(self, cache):
        methods = cache["OpenReviewClient"]
        assert "post_note_edit" in methods
        params = methods["post_note_edit"]["params"]
        param_names = [p["name"] for p in params]
        assert "invitation" in param_names
        assert "signatures" in param_names
        assert "note" in param_names
        assert "await_process" in param_names

    def test_captures_docstrings(self, cache):
        # OpenReviewClient.__init__ has a docstring
        methods = cache["OpenReviewClient"]
        init_info = methods["__init__"]
        assert init_info["docstring"] is not None
        assert len(init_info["docstring"]) > 0

    def test_skips_private_methods(self, cache):
        methods = cache["OpenReviewClient"]
        for method_name in methods:
            assert not method_name.startswith("_") or method_name == "__init__", (
                f"Private method included: {method_name}"
            )


class TestSearchMethods:
    def test_exact_name_match(self, cache):
        results = search_methods("post_note_edit", None, cache)
        assert len(results) > 0
        assert results[0]["name"] == "post_note_edit"

    def test_partial_name_match(self, cache):
        results = search_methods("post_note", None, cache)
        names = [r["name"] for r in results]
        assert "post_note_edit" in names

    def test_docstring_match(self, cache):
        # "baseurl" appears in OpenReviewClient.__init__ docstring
        results = search_methods("baseurl", None, cache)
        assert len(results) > 0

    def test_class_filter(self, cache):
        results = search_methods("setup", "Venue", cache)
        for r in results:
            assert r["class_name"] == "Venue"

    def test_max_results(self, cache):
        results = search_methods("get", None, cache)
        assert len(results) <= 15

    def test_relevance_ordering(self, cache):
        results = search_methods("post_note_edit", None, cache)
        # Exact match should be first
        assert results[0]["name"] == "post_note_edit"

    def test_no_match_returns_empty(self, cache):
        results = search_methods("zzz_nonexistent_zzz", None, cache)
        assert results == []


class TestGetMethodDetails:
    def test_returns_full_info(self, cache):
        results = get_method_details("post_note_edit", cache)
        assert len(results) > 0
        detail = results[0]
        assert detail["class_name"] == "OpenReviewClient"
        assert detail["name"] == "post_note_edit"
        assert "params" in detail
        assert "signature" in detail

    def test_partial_match(self, cache):
        results = get_method_details("get_all", cache)
        names = [r["name"] for r in results]
        assert "get_all_notes" in names

    def test_no_match_returns_empty(self, cache):
        results = get_method_details("zzz_nonexistent_zzz", cache)
        assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && python -m pytest tests/test_introspection.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.introspection'`

- [ ] **Step 3: Commit**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git add tests/test_introspection.py
git commit -m "test: add Layer 1 introspection tests (failing)"
```

---

### Task 3: Write Layer 2 tests — knowledge

**Files:**
- Create: `tests/test_knowledge.py`

- [ ] **Step 1: Write all knowledge tests**

Create `tests/test_knowledge.py`:

```python
"""Tests for static knowledge parsing (llm.txt + examples.md)."""

import os
import pytest
from src.knowledge import KnowledgeBase, load_knowledge, search_best_practices, search_examples, get_workflow


class TestLoadKnowledge:
    def test_parses_llm_txt_sections(self, llm_txt_path, examples_md_path):
        kb = load_knowledge(llm_txt_path, examples_md_path)
        # Fixture has 4 sections: Authentication, Content Structure, Conference Workflow, Anti-Patterns
        assert len(kb.practices) == 4
        assert "Authentication" in kb.practices
        assert "Content Structure" in kb.practices
        assert "Conference Workflow" in kb.practices
        assert "Anti-Patterns to Avoid" in kb.practices

    def test_parses_examples_md_sections(self, llm_txt_path, examples_md_path):
        kb = load_knowledge(llm_txt_path, examples_md_path)
        # Fixture has sections: Authentication, Notes, Conference Workflow
        # with subsections: Connect to production, Token-based auth, Submit a paper, etc.
        assert "Authentication" in kb.examples
        assert "Notes" in kb.examples
        assert "Conference Workflow" in kb.examples

    def test_missing_file_raises(self, examples_md_path):
        with pytest.raises(FileNotFoundError):
            load_knowledge("/nonexistent/path/llm.txt", examples_md_path)


@pytest.fixture(scope="module")
def kb():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    return load_knowledge(
        os.path.join(fixtures_dir, "llm.txt"),
        os.path.join(fixtures_dir, "examples.md"),
    )


class TestSearchBestPractices:
    def test_header_match(self, kb):
        result = search_best_practices("Authentication", kb)
        assert "Token auth" in result
        assert "username" in result.lower()

    def test_content_match(self, kb):
        result = search_best_practices("token", kb)
        assert len(result) > 0
        assert "token" in result.lower()

    def test_case_insensitive(self, kb):
        result = search_best_practices("AUTHENTICATION", kb)
        assert "Token auth" in result

    def test_no_match(self, kb):
        result = search_best_practices("zzz_nonexistent_zzz", kb)
        assert result == ""

    def test_header_ranked_above_content(self, kb):
        # "Authentication" is a header; "token" appears in content of Auth AND Anti-Patterns
        result = search_best_practices("Authentication", kb)
        # The Authentication section should come first
        lines = result.strip().split("\n")
        assert "Authentication" in lines[0]


class TestSearchExamples:
    def test_finds_code_blocks(self, kb):
        result = search_examples("submit paper", kb)
        assert "```python" in result
        assert "post_note_edit" in result

    def test_no_match(self, kb):
        result = search_examples("zzz_nonexistent_zzz", kb)
        assert result == ""


class TestGetWorkflow:
    def test_conference(self, kb):
        result = get_workflow("conference", kb)
        assert "Venue Request" in result
        assert "Deploy" in result
        # Should also include code examples
        assert "```python" in result

    def test_journal(self, kb):
        # Fixture doesn't have journal, should return empty or partial
        result = get_workflow("journal", kb)
        # No journal section in fixture, so empty
        assert result == ""

    def test_specific_stage(self, kb):
        result = get_workflow("review", kb)
        # Should match review-related content from both practices and examples
        assert len(result) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && python -m pytest tests/test_knowledge.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.knowledge'`

- [ ] **Step 3: Commit**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git add tests/test_knowledge.py
git commit -m "test: add Layer 2 knowledge tests (failing)"
```

---

### Task 4: Write Layer 3 tests — MCP tools

**Files:**
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write all tool tests**

Create `tests/test_tools.py`:

```python
"""Tests for MCP tools via FastMCP (no server startup needed)."""

import pytest
import pytest_asyncio

# These tests will import after server.py is implemented
from src.server import mcp


@pytest.mark.asyncio
async def test_search_api_returns_results():
    async with mcp.test_client() as client:
        result = await client.call_tool("search_api", {"query": "post_note"})
        text = result[0].text
        assert "post_note_edit" in text


@pytest.mark.asyncio
async def test_search_api_with_class_filter():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "search_api", {"query": "setup", "class_name": "Venue"}
        )
        text = result[0].text
        # All results should be from Venue class
        assert "Venue" in text
        assert "OpenReviewClient" not in text


@pytest.mark.asyncio
async def test_get_method_signature_returns_details():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "get_method_signature", {"method_name": "post_note_edit"}
        )
        text = result[0].text
        assert "post_note_edit" in text
        assert "invitation" in text
        assert "signatures" in text
        assert "await_process" in text


@pytest.mark.asyncio
async def test_get_best_practices_returns_section():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "get_best_practices", {"topic": "authentication"}
        )
        text = result[0].text
        assert "token" in text.lower()


@pytest.mark.asyncio
async def test_get_code_example_returns_snippet():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "get_code_example", {"operation": "submit paper"}
        )
        text = result[0].text
        assert "post_note_edit" in text
        assert "```python" in text


@pytest.mark.asyncio
async def test_get_workflow_guide_conference():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "get_workflow_guide", {"workflow_type": "conference"}
        )
        text = result[0].text
        assert "Venue Request" in text or "Deploy" in text


@pytest.mark.asyncio
async def test_get_workflow_guide_journal():
    async with mcp.test_client() as client:
        result = await client.call_tool(
            "get_workflow_guide", {"workflow_type": "journal"}
        )
        text = result[0].text
        assert "Submit" in text or "Review" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && python -m pytest tests/test_tools.py -v`
Expected: FAIL with `ImportError` (server.py not yet rewritten)

- [ ] **Step 3: Commit**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git add tests/test_tools.py
git commit -m "test: add Layer 3 MCP tool tests (failing)"
```

---

### Task 5: Implement introspection.py

**Files:**
- Create: `src/introspection.py`

- [ ] **Step 1: Implement introspection module**

Create `src/introspection.py`:

```python
"""Live introspection of the openreview-py library using Python's inspect module."""

import inspect
from typing import Any


# Classes to introspect, mapped as (module_path, class_name)
TARGET_CLASSES = [
    ("openreview.api.client", "OpenReviewClient"),
    ("openreview.openreview", "Client"),
    ("openreview.api.client", "Note"),
    ("openreview.api.client", "Invitation"),
    ("openreview.api.client", "Edge"),
    ("openreview.api.client", "Group"),
    ("openreview.api.client", "Tag"),
    ("openreview.api.client", "Edit"),
    ("openreview.openreview", "Profile"),
    ("openreview.venue", "Venue"),
]


def _extract_params(sig: inspect.Signature) -> list[dict[str, Any]]:
    """Extract parameter info from a signature."""
    params = []
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        info: dict[str, Any] = {"name": name}
        if param.annotation != inspect.Parameter.empty:
            info["type"] = str(param.annotation)
        if param.default != inspect.Parameter.empty:
            info["default"] = repr(param.default)
        params.append(info)
    return params


def introspect_library() -> dict[str, dict[str, dict[str, Any]]]:
    """Import openreview and introspect all target classes.

    Returns a dict keyed by class name, where each value is a dict
    of method_name -> method_info.
    """
    import importlib

    cache: dict[str, dict[str, dict[str, Any]]] = {}

    for module_path, class_name in TARGET_CLASSES:
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
        except (ImportError, AttributeError):
            continue

        methods: dict[str, dict[str, Any]] = {}
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            # Skip private methods except __init__
            if name.startswith("_") and name != "__init__":
                continue

            try:
                sig = inspect.signature(method)
            except (ValueError, TypeError):
                sig = None

            docstring = inspect.getdoc(method)

            methods[name] = {
                "name": name,
                "class_name": class_name,
                "module": module_path,
                "signature": str(sig) if sig else "()",
                "params": _extract_params(sig) if sig else [],
                "docstring": docstring,
            }

        cache[class_name] = methods

    return cache


def search_methods(
    query: str,
    class_name: str | None,
    cache: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Search methods by keyword with relevance ranking.

    Ranking: exact name match > name contains > docstring contains > param contains.
    Returns at most 15 results.
    """
    query_lower = query.lower()
    exact = []
    name_contains = []
    doc_contains = []
    param_contains = []

    classes_to_search = (
        {class_name: cache[class_name]} if class_name and class_name in cache else cache
    )

    for cls_name, methods in classes_to_search.items():
        for method_name, info in methods.items():
            if method_name == "__init__":
                continue

            if method_name.lower() == query_lower:
                exact.append(info)
            elif query_lower in method_name.lower():
                name_contains.append(info)
            elif info.get("docstring") and query_lower in info["docstring"].lower():
                doc_contains.append(info)
            elif any(query_lower in p["name"].lower() for p in info.get("params", [])):
                param_contains.append(info)

    results = exact + name_contains + doc_contains + param_contains
    return results[:15]


def get_method_details(
    method_name: str,
    cache: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Get full details for methods matching the given name.

    Exact matches first, then partial matches.
    """
    method_lower = method_name.lower()
    exact = []
    partial = []

    for cls_name, methods in cache.items():
        for name, info in methods.items():
            if name.lower() == method_lower:
                exact.append(info)
            elif method_lower in name.lower() and name != "__init__":
                partial.append(info)

    return exact + partial
```

- [ ] **Step 2: Run Layer 1 tests**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && python -m pytest tests/test_introspection.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git add src/introspection.py
git commit -m "feat: implement live introspection of openreview-py"
```

---

### Task 6: Implement knowledge.py

**Files:**
- Create: `src/knowledge.py`

- [ ] **Step 1: Implement knowledge module**

Create `src/knowledge.py`:

```python
"""Static knowledge parser for llm.txt and examples.md."""

import re
from dataclasses import dataclass, field


@dataclass
class KnowledgeBase:
    """Indexed sections from llm.txt and examples.md."""

    practices: dict[str, str] = field(default_factory=dict)
    examples: dict[str, str] = field(default_factory=dict)


def _parse_sections(content: str, level: str = "## ") -> dict[str, str]:
    """Split markdown content into sections by header level.

    Returns dict of {header_text: section_content_including_subsections}.
    """
    sections: dict[str, str] = {}
    current_header = None
    current_lines: list[str] = []

    for line in content.split("\n"):
        if line.startswith(level) and not line.startswith(level + "#"):
            if current_header is not None:
                sections[current_header] = "\n".join(current_lines).strip()
            current_header = line[len(level):].strip()
            current_lines = [line]
        elif current_header is not None:
            current_lines.append(line)

    if current_header is not None:
        sections[current_header] = "\n".join(current_lines).strip()

    return sections


def load_knowledge(llm_txt_path: str, examples_md_path: str) -> KnowledgeBase:
    """Parse llm.txt and examples.md into an indexed KnowledgeBase."""
    if not _file_exists(llm_txt_path):
        raise FileNotFoundError(f"llm.txt not found at: {llm_txt_path}")
    if not _file_exists(examples_md_path):
        raise FileNotFoundError(f"examples.md not found at: {examples_md_path}")

    with open(llm_txt_path, "r") as f:
        llm_content = f.read()
    with open(examples_md_path, "r") as f:
        examples_content = f.read()

    return KnowledgeBase(
        practices=_parse_sections(llm_content, "## "),
        examples=_parse_sections(examples_content, "## "),
    )


def _file_exists(path: str) -> bool:
    import os
    return os.path.isfile(path)


def search_best_practices(topic: str, kb: KnowledgeBase) -> str:
    """Search llm.txt sections by topic. Header matches ranked above content matches."""
    topic_lower = topic.lower()
    header_matches = []
    content_matches = []

    for header, content in kb.practices.items():
        if topic_lower in header.lower():
            header_matches.append(content)
        elif topic_lower in content.lower():
            content_matches.append(content)

    results = header_matches + content_matches
    if not results:
        return ""
    return "\n\n---\n\n".join(results)


def search_examples(operation: str, kb: KnowledgeBase) -> str:
    """Search examples.md sections by operation keyword."""
    operation_lower = operation.lower()
    matches = []

    for header, content in kb.examples.items():
        if operation_lower in header.lower() or operation_lower in content.lower():
            matches.append(content)

    if not matches:
        return ""
    return "\n\n---\n\n".join(matches)


def get_workflow(workflow_type: str, kb: KnowledgeBase) -> str:
    """Get workflow guide combining practices and examples.

    For 'conference' or 'journal': returns the full workflow section + matching examples.
    For a specific stage: returns matching content from both.
    """
    wf_lower = workflow_type.lower()
    parts = []

    # Search practices for workflow section
    for header, content in kb.practices.items():
        if wf_lower in header.lower():
            parts.append(content)

    # Search examples for matching code
    for header, content in kb.examples.items():
        if wf_lower in header.lower():
            parts.append(content)

    # If no direct match, search content for the keyword
    if not parts:
        for header, content in kb.practices.items():
            if wf_lower in content.lower():
                parts.append(content)
        for header, content in kb.examples.items():
            if wf_lower in content.lower():
                parts.append(content)

    if not parts:
        return ""
    return "\n\n---\n\n".join(parts)
```

- [ ] **Step 2: Run Layer 2 tests**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && python -m pytest tests/test_knowledge.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git add src/knowledge.py
git commit -m "feat: implement knowledge parser for llm.txt and examples.md"
```

---

### Task 7: Implement server.py (rewrite)

**Files:**
- Rewrite: `src/server.py`

- [ ] **Step 1: Rewrite server.py with 5 tools**

Replace the contents of `src/server.py` with:

```python
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
```

- [ ] **Step 2: Run Layer 3 tests**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && OPENREVIEW_KNOWLEDGE_PATH=/Users/cmondragonch/Documents/openreview-py python -m pytest tests/test_tools.py -v`
Expected: All tests PASS

- [ ] **Step 3: Run all tests**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && OPENREVIEW_KNOWLEDGE_PATH=/Users/cmondragonch/Documents/openreview-py python -m pytest tests/ -v`
Expected: All 3 layers pass

- [ ] **Step 4: Commit**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git add src/server.py
git commit -m "feat: rewrite server with 5 focused tools (introspection + knowledge)"
```

---

### Task 8: Remove old introspect.py

**Files:**
- Delete: `src/introspect.py`

- [ ] **Step 1: Remove old static metadata file**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git rm src/introspect.py
```

- [ ] **Step 2: Run all tests to verify nothing broke**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && OPENREVIEW_KNOWLEDGE_PATH=/Users/cmondragonch/Documents/openreview-py python -m pytest tests/ -v`
Expected: All tests still pass

- [ ] **Step 3: Commit**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git commit -m "chore: remove old static introspect.py (replaced by live introspection)"
```

---

### Task 9: Update CLAUDE.md and README.md

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

- [ ] **Step 1: Update CLAUDE.md**

Replace the project structure and tool descriptions in `CLAUDE.md` to reflect the new 5-tool architecture, new file structure (`introspection.py`, `knowledge.py`), and the `OPENREVIEW_KNOWLEDGE_PATH` environment variable.

- [ ] **Step 2: Update README.md**

Update the tool listing, quick start instructions, and architecture description. Include the environment variable for pointing to the knowledge files.

- [ ] **Step 3: Commit**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git add CLAUDE.md README.md
git commit -m "docs: update CLAUDE.md and README.md for new tool architecture"
```

---

### Task 10: End-to-end verification

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && OPENREVIEW_KNOWLEDGE_PATH=/Users/cmondragonch/Documents/openreview-py python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Start the server manually**

Run: `cd /Users/cmondragonch/Documents/openreview-mcp && OPENREVIEW_KNOWLEDGE_PATH=/Users/cmondragonch/Documents/openreview-py uv run src/server.py`
Expected: Server starts, logs show introspected classes and loaded knowledge sections

- [ ] **Step 3: Verify MCP tool listing**

Connect via Claude Code MCP config or use `fastmcp` CLI to list tools. Verify all 5 tools appear: `search_api`, `get_method_signature`, `get_best_practices`, `get_code_example`, `get_workflow_guide`.
