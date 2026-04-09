# Decouple openreview-mcp from openreview-tools-mcp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor `openreview-mcp` into a publicly-distributable, knowledge-only MCP server that exposes a reusable `register_knowledge_tools(mcp)` function and has zero references to `openreview-tools-mcp`. Bundles `llm.txt` and `examples.md` inside the package so a bare install works without cloning a second repo.

**Architecture:** Rename `src/` to a properly-named `openreview_mcp/` package. Split the tool registration logic out of `server.py` into a pure `registration.py` module that has zero import side effects, so downstream consumers can `from openreview_mcp import register_knowledge_tools` and mount the knowledge tools onto their own `FastMCP` instance. The standalone `server.py` becomes a thin entry point that creates its own `FastMCP`, calls `register_knowledge_tools`, and runs it. Bundled knowledge files live under `openreview_mcp/knowledge_files/` and serve as the default when `OPENREVIEW_KNOWLEDGE_PATH` is unset.

**Tech Stack:** Python 3.11+, FastMCP, openreview-py, pytest, hatchling, Docker

**Working directories:**
- Main repo: `/Users/cmondragonch/Documents/openreview-mcp`
- Reference (real knowledge files): `/Users/cmondragonch/Documents/openreview-py`
- Reference (downstream consumer for verification): `/Users/cmondragonch/Documents/openreview-tools-mcp`

**Scope note:** This plan covers ONLY the `openreview-mcp` refactor + release. Wiring `openreview-tools-mcp` to depend on the new `register_knowledge_tools` is a separate follow-up plan.

---

## File Structure

```
openreview-mcp/
├── src/                               # DELETE (renamed)
├── openreview_mcp/                    # CREATE (renamed from src/)
│   ├── __init__.py                    # MODIFY: re-export register_knowledge_tools
│   ├── introspection.py               # KEEP: update imports only
│   ├── knowledge.py                   # KEEP: update imports only
│   ├── registration.py                # CREATE: register_knowledge_tools(mcp)
│   ├── server.py                      # REWRITE: thin entry point
│   └── knowledge_files/               # CREATE: bundled defaults
│       ├── llm.txt                    # CREATE: copy from openreview-py
│       └── examples.md                # CREATE: copy from openreview-py
├── tests/
│   ├── test_introspection.py          # MODIFY: update imports
│   ├── test_knowledge.py              # MODIFY: update imports
│   ├── test_registration.py           # CREATE: new — test register_knowledge_tools
│   ├── test_tools.py                  # REWRITE: use FastMCP fixture pattern
│   └── test_bundled_knowledge.py      # CREATE: verify bundled files load
├── pyproject.toml                     # MODIFY: name, packages target, entry point
├── Dockerfile                         # MODIFY: remove plugin install block
├── build-docker.sh                    # DELETE (existed only for plugin copy)
├── README.md                          # MODIFY: remove plugin section
├── CLAUDE.md                          # MODIFY: remove build-docker.sh refs if any
├── openreview_mcp/CLAUDE.md           # MODIFY (post-rename): refresh module doc
├── tests/CLAUDE.md                    # MODIFY: update for new test files
└── docs/superpowers/plans/2026-04-09-decouple-from-tools-mcp.md  # this file
```

---

## Task 1: Create worktree and baseline current state

**Files:**
- None modified — just verification

- [ ] **Step 1: Create a dedicated worktree for this refactor**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git worktree add ../openreview-mcp-decouple -b refactor/decouple-from-tools-mcp
cd ../openreview-mcp-decouple
```

Expected: new worktree directory at `../openreview-mcp-decouple` on branch `refactor/decouple-from-tools-mcp`.

- [ ] **Step 2: Install the package in editable mode with dev extras inside the worktree**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp-decouple
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Expected: successful install, including `openreview-py` pulled from git.

- [ ] **Step 3: Run the full test suite to confirm baseline green**

```bash
OPENREVIEW_KNOWLEDGE_PATH=/Users/cmondragonch/Documents/openreview-py \
  .venv/bin/python -m pytest tests/ -v
```

Expected: all tests pass. Record the test count so later tasks can compare. **If anything is red before we start, stop and investigate** — we need a known-good baseline.

- [ ] **Step 4: Commit a baseline marker (optional but useful for bisecting)**

```bash
git commit --allow-empty -m "chore: baseline for decouple refactor"
```

---

## Task 2: Rename `src/` to `openreview_mcp/` (packaging fix)

**Files:**
- Move: `src/` → `openreview_mcp/`
- Modify: `openreview_mcp/server.py` — import statements
- Modify: `tests/test_introspection.py` — import statements
- Modify: `tests/test_knowledge.py` — import statements
- Modify: `tests/test_tools.py` — import statements
- Modify: `pyproject.toml:31-32` — wheel packages target
- Modify: `pyproject.toml:49-50` — entry point
- Modify: `Dockerfile:10` — `COPY src/ src/` → `COPY openreview_mcp/ openreview_mcp/`

- [ ] **Step 1: Move the directory**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp-decouple
git mv src openreview_mcp
```

Expected: `openreview_mcp/` now contains `__init__.py`, `introspection.py`, `knowledge.py`, `server.py`, and (from the earlier CLAUDE.md work) `CLAUDE.md`.

- [ ] **Step 2: Update imports in `openreview_mcp/server.py`**

Replace lines 9-10:

```python
from src.introspection import introspect_library, search_methods, get_method_details
from src.knowledge import load_knowledge, search_best_practices, search_examples, get_workflow
```

With:

```python
from openreview_mcp.introspection import introspect_library, search_methods, get_method_details
from openreview_mcp.knowledge import load_knowledge, search_best_practices, search_examples, get_workflow
```

- [ ] **Step 3: Update imports in test files**

In `tests/test_introspection.py:4`, replace:
```python
from src.introspection import introspect_library, search_methods, get_method_details
```
with:
```python
from openreview_mcp.introspection import introspect_library, search_methods, get_method_details
```

In `tests/test_knowledge.py:5`, replace:
```python
from src.knowledge import KnowledgeBase, load_knowledge, search_best_practices, search_examples, get_workflow
```
with:
```python
from openreview_mcp.knowledge import KnowledgeBase, load_knowledge, search_best_practices, search_examples, get_workflow
```

In `tests/test_tools.py:3`, replace:
```python
from src.server import search_api, get_method_signature, get_best_practices, get_code_example, get_workflow_guide
```
with:
```python
from openreview_mcp.server import search_api, get_method_signature, get_best_practices, get_code_example, get_workflow_guide
```

(Note: `test_tools.py` will be rewritten in Task 5. For now, just get the imports landing on the renamed module so this task's commits stay green.)

- [ ] **Step 4: Update `pyproject.toml` packaging target**

Replace lines 31-32:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src"]
```
with:
```toml
[tool.hatch.build.targets.wheel]
packages = ["openreview_mcp"]
```

Replace lines 49-50:
```toml
[project.scripts]
openreview-mcp = "src.server:main"
```
with:
```toml
[project.scripts]
openreview-mcp = "openreview_mcp.server:main"
```

- [ ] **Step 5: Update `Dockerfile` copy target**

Replace line 10:
```dockerfile
COPY src/ src/
```
with:
```dockerfile
COPY openreview_mcp/ openreview_mcp/
```

- [ ] **Step 6: Reinstall the package (the entry point script path changed)**

```bash
.venv/bin/pip install -e ".[dev]"
```

Expected: successful install. The `openreview-mcp` CLI shim now points at `openreview_mcp.server:main`.

- [ ] **Step 7: Run the full test suite**

```bash
OPENREVIEW_KNOWLEDGE_PATH=/Users/cmondragonch/Documents/openreview-py \
  .venv/bin/python -m pytest tests/ -v
```

Expected: same number of tests pass as in Task 1 Step 3. Nothing changed except import paths.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor: rename src/ to openreview_mcp/ for proper package name

Previously the wheel installed the package as literal 'src', forcing
imports like 'from src.introspection import ...'. This makes the package
importable from downstream consumers as 'openreview_mcp'."
```

---

## Task 3: Bundle `llm.txt` and `examples.md` inside the package

**Files:**
- Create: `openreview_mcp/knowledge_files/llm.txt` (copied from `openreview-py`)
- Create: `openreview_mcp/knowledge_files/examples.md` (copied from `openreview-py`)
- Create: `tests/test_bundled_knowledge.py`
- Modify: `openreview_mcp/server.py` — knowledge path resolution
- Modify: `Dockerfile` — the `OPENREVIEW_KNOWLEDGE_PATH` env var no longer needed as a bind-mount default

- [ ] **Step 1: Copy the real knowledge files into the package**

```bash
mkdir -p openreview_mcp/knowledge_files
cp /Users/cmondragonch/Documents/openreview-py/llm.txt openreview_mcp/knowledge_files/llm.txt
cp /Users/cmondragonch/Documents/openreview-py/examples.md openreview_mcp/knowledge_files/examples.md
```

Expected: two files present at `openreview_mcp/knowledge_files/`. Verify with `ls -la openreview_mcp/knowledge_files/`.

- [ ] **Step 2: Write the failing test for bundled knowledge loading**

Create `tests/test_bundled_knowledge.py`:

```python
"""Verifies the bundled knowledge files ship with the package and load correctly."""

import os

from openreview_mcp.knowledge import load_knowledge


def test_bundled_knowledge_files_exist():
    """The package must ship with knowledge_files/llm.txt and examples.md."""
    import openreview_mcp
    pkg_dir = os.path.dirname(os.path.abspath(openreview_mcp.__file__))
    bundled_dir = os.path.join(pkg_dir, "knowledge_files")
    assert os.path.isfile(os.path.join(bundled_dir, "llm.txt"))
    assert os.path.isfile(os.path.join(bundled_dir, "examples.md"))


def test_bundled_knowledge_loads_non_empty():
    """Loading the bundled files must yield non-empty practices and examples."""
    import openreview_mcp
    pkg_dir = os.path.dirname(os.path.abspath(openreview_mcp.__file__))
    bundled_dir = os.path.join(pkg_dir, "knowledge_files")

    kb = load_knowledge(
        os.path.join(bundled_dir, "llm.txt"),
        os.path.join(bundled_dir, "examples.md"),
    )

    assert len(kb.practices) > 0, "Bundled llm.txt produced zero practice sections"
    assert len(kb.examples) > 0, "Bundled examples.md produced zero example sections"
```

- [ ] **Step 3: Run the new test to verify it passes (files are already in place)**

```bash
.venv/bin/python -m pytest tests/test_bundled_knowledge.py -v
```

Expected: both tests pass. If `test_bundled_knowledge_files_exist` fails, the `cp` step didn't land — re-check paths.

- [ ] **Step 4: Update `openreview_mcp/server.py` to use bundled files as the default knowledge path**

Replace the current lines 15-18:

```python
KNOWLEDGE_PATH = os.environ.get(
    "OPENREVIEW_KNOWLEDGE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "openreview-py"),
)
```

with:

```python
_BUNDLED_KNOWLEDGE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "knowledge_files"
)
KNOWLEDGE_PATH = os.environ.get("OPENREVIEW_KNOWLEDGE_PATH", _BUNDLED_KNOWLEDGE_DIR)
```

This keeps the env-var override working (developers who want to point at a live `openreview-py` clone still can) but defaults to the bundled directory for bare installs.

- [ ] **Step 5: Update `Dockerfile` to drop the external knowledge default**

Replace line 25:
```dockerfile
ENV OPENREVIEW_KNOWLEDGE_PATH=/knowledge
```
with:
```dockerfile
# Knowledge files are bundled inside the package. To override with a live
# openreview-py clone, pass -e OPENREVIEW_KNOWLEDGE_PATH=/path at runtime.
```

The env var is no longer needed as a baked-in default. The bundled files handle the zero-config path.

- [ ] **Step 6: Run the full test suite with NO env var to verify the default path works end-to-end**

```bash
unset OPENREVIEW_KNOWLEDGE_PATH
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests pass, including the tests in `test_knowledge.py` which use the fixture directory (unaffected), the new `test_bundled_knowledge.py` tests, and `test_tools.py` which imports `openreview_mcp.server` — the module-level `load_knowledge` call now hits the bundled files.

- [ ] **Step 7: Commit**

```bash
git add openreview_mcp/knowledge_files/ openreview_mcp/server.py Dockerfile tests/test_bundled_knowledge.py
git commit -m "feat: bundle llm.txt and examples.md inside the package

Bare 'pip install openreview-mcp' now works with zero config — no need
to clone openreview-py separately just to get the knowledge files.
OPENREVIEW_KNOWLEDGE_PATH still overrides for developers pointing at a
live openreview-py checkout."
```

---

## Task 4: Extract `register_knowledge_tools(mcp)` into a reusable module

**Files:**
- Create: `openreview_mcp/registration.py`
- Modify: `openreview_mcp/__init__.py` — re-export
- Modify: `openreview_mcp/server.py` — shrink to thin entry point
- Create: `tests/test_registration.py`

- [ ] **Step 1: Write the failing test for `register_knowledge_tools`**

Create `tests/test_registration.py`:

```python
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
        """Each returned handle must have a .fn attribute pointing at the underlying function."""
        mcp = FastMCP("test")
        handles = register_knowledge_tools(mcp)

        result = handles["search_api"].fn(query="post_note")
        assert "post_note_edit" in result
```

- [ ] **Step 2: Run the test to verify it fails with `ImportError`**

```bash
.venv/bin/python -m pytest tests/test_registration.py -v
```

Expected: FAIL with `ImportError: cannot import name 'register_knowledge_tools' from 'openreview_mcp'`.

- [ ] **Step 3: Create `openreview_mcp/registration.py`**

```python
"""Reusable registration of the knowledge tools onto a FastMCP instance.

This module has zero import side effects — no module-level FastMCP is created,
no knowledge is loaded at import time. Downstream consumers (e.g.
openreview-tools-mcp) can safely `from openreview_mcp import register_knowledge_tools`
and mount the tools onto their own server.
"""

import logging
import os
from typing import Any, Callable

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
) -> dict[str, Callable]:
    """Register the 5 knowledge tools onto the given FastMCP instance.

    Reads/introspects the installed `openreview-py` and loads the bundled (or
    override) knowledge files at call time — not at import time.

    Args:
        mcp: The FastMCP server to register tools on.
        knowledge_path: Optional directory containing llm.txt and examples.md.
            Falls back to the OPENREVIEW_KNOWLEDGE_PATH env var, then to the
            knowledge files bundled inside the package.

    Returns:
        A dict mapping tool name to the registered tool handle (each handle has
        a `.fn` attribute exposing the underlying function for direct testing).
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
```

- [ ] **Step 4: Update `openreview_mcp/__init__.py` to re-export**

Replace the current single-line contents:

```python
# Package init for openreview_py_mcp
```

with:

```python
"""openreview-mcp — knowledge-only MCP server for the openreview-py library."""

from openreview_mcp.registration import register_knowledge_tools

__all__ = ["register_knowledge_tools"]
```

- [ ] **Step 5: Run the registration test to verify it passes**

```bash
.venv/bin/python -m pytest tests/test_registration.py -v
```

Expected: all three `TestRegisterKnowledgeTools` tests pass.

- [ ] **Step 6: Rewrite `openreview_mcp/server.py` as a thin entry point**

Replace the entire file contents with:

```python
"""Standalone FastMCP server entry point for openreview-mcp."""

import logging

from fastmcp import FastMCP

from openreview_mcp.registration import register_knowledge_tools

logger = logging.getLogger("openreview_mcp")

mcp = FastMCP(
    name="OpenReview Python Library Expert",
    instructions=(
        "Expert assistant for the openreview-py Python library. "
        "Use these tools to find API methods, best practices, code examples, "
        "and workflow guides for building with OpenReview."
    ),
)

# Register the 5 knowledge tools onto this server's FastMCP instance.
# Uses the bundled knowledge files unless OPENREVIEW_KNOWLEDGE_PATH overrides.
register_knowledge_tools(mcp)


def main() -> None:
    """Start the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

Note what changed from the original: no formatting helpers (now in `registration.py`), no introspection cache or knowledge base at module level (now inside `register_knowledge_tools`), no tool function definitions (now inside `register_knowledge_tools`), no plugin try/except (Task 5 deletes it from the Dockerfile; it's already gone from this rewrite). The file went from ~180 lines to ~30.

- [ ] **Step 7: Run the full test suite**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: the new `test_registration.py` tests pass. `test_introspection.py` and `test_knowledge.py` still pass (unchanged). `test_tools.py` will **fail** because it imports `search_api`, etc. as module-level names from `openreview_mcp.server` — those no longer exist. That's expected — Task 5 rewrites `test_tools.py` to use the new pattern.

Temporarily skip `test_tools.py` to confirm everything else is green:

```bash
.venv/bin/python -m pytest tests/ -v --ignore=tests/test_tools.py
```

Expected: all remaining tests pass.

- [ ] **Step 8: Commit**

```bash
git add openreview_mcp/registration.py openreview_mcp/__init__.py openreview_mcp/server.py tests/test_registration.py
git commit -m "feat: extract register_knowledge_tools into reusable module

Downstream consumers can now 'from openreview_mcp import register_knowledge_tools'
and mount the 5 knowledge tools onto their own FastMCP instance with zero
import side effects. server.py is now a thin standalone entry point.

test_tools.py is temporarily broken and will be rewritten in the next commit
to use the FastMCP fixture pattern."
```

---

## Task 5: Rewrite `test_tools.py` using the FastMCP fixture pattern

**Files:**
- Rewrite: `tests/test_tools.py`

- [ ] **Step 1: Rewrite `tests/test_tools.py` to use the return value of `register_knowledge_tools`**

Replace the entire file contents with:

```python
"""Tests for the 5 MCP knowledge tools via register_knowledge_tools."""

import pytest
from fastmcp import FastMCP

from openreview_mcp import register_knowledge_tools


@pytest.fixture(scope="module")
def tools():
    """Register the knowledge tools onto a fresh FastMCP and return the tool handles."""
    mcp = FastMCP("test")
    return register_knowledge_tools(mcp)


def test_search_api_returns_results(tools):
    text = tools["search_api"].fn(query="post_note")
    assert "post_note_edit" in text


def test_search_api_with_class_filter(tools):
    text = tools["search_api"].fn(query="setup", class_name="Venue")
    assert "Venue" in text
    assert "OpenReviewClient" not in text


def test_get_method_signature_returns_details(tools):
    text = tools["get_method_signature"].fn(method_name="post_note_edit")
    assert "post_note_edit" in text
    assert "invitation" in text
    assert "signatures" in text
    assert "await_process" in text


def test_get_best_practices_returns_section(tools):
    text = tools["get_best_practices"].fn(topic="authentication")
    assert "token" in text.lower()


def test_get_code_example_returns_snippet(tools):
    text = tools["get_code_example"].fn(operation="submit paper")
    assert "post_note_edit" in text
    assert "```python" in text


def test_get_workflow_guide_conference(tools):
    text = tools["get_workflow_guide"].fn(workflow_type="conference")
    assert "Venue Request" in text or "Deploy" in text


def test_get_workflow_guide_journal(tools):
    text = tools["get_workflow_guide"].fn(workflow_type="journal")
    assert "Submit" in text or "Review" in text
```

- [ ] **Step 2: Run the rewritten test file**

```bash
.venv/bin/python -m pytest tests/test_tools.py -v
```

Expected: all 7 tests pass against the bundled knowledge files.

- [ ] **Step 3: Run the full suite with no env var override**

```bash
unset OPENREVIEW_KNOWLEDGE_PATH
.venv/bin/python -m pytest tests/ -v
```

Expected: every test passes, no env var needed. This proves the public install story works.

- [ ] **Step 4: Commit**

```bash
git add tests/test_tools.py
git commit -m "test: rewrite test_tools.py to use register_knowledge_tools pattern

Tools are no longer module-level names on openreview_mcp.server — they
are created inside register_knowledge_tools. Tests now use a FastMCP
fixture + the returned tool handle dict, matching the pattern used by
openreview-tools-mcp's test suite."
```

---

## Task 6: Remove the `openreview-tools-mcp` plugin hook

**Files:**
- Modify: `Dockerfile:13-23` — delete plugin install block
- Delete: `build-docker.sh`
- Modify: `README.md:12-18` — delete "with optional tools plugin" section

Note: `openreview_mcp/server.py` already has no plugin hook (Task 4 rewrote it from scratch without one).

- [ ] **Step 1: Grep for any remaining references to `openreview_tools` or `openreview-tools-mcp` in the codebase**

```bash
grep -rn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ "openreview[-_]tools" .
```

Expected matches (each will be deleted in this task):
- `Dockerfile` — the plugin install block
- `build-docker.sh` — the sibling-copy wrapper
- `README.md` — the "with optional tools plugin" quick-start variant

**If anything outside those three files matches, stop and review** — we don't want to leave dangling references.

- [ ] **Step 2: Simplify the Dockerfile — remove the plugin install block**

Delete lines 13-23 of `Dockerfile`:

```dockerfile
# Install tools plugin if present (optional)
# To include it: cp -r ../openreview-tools-mcp tools-plugin
# Then build normally: docker build -t openreview-mcp .
# Without it, the image works fine — just no live API tools.
COPY tools-plugi[n] /tmp/tools-plugin/
RUN if [ -f /tmp/tools-plugin/pyproject.toml ]; then \
        pip install --no-cache-dir /tmp/tools-plugin/ && \
        echo "openreview-tools-mcp plugin installed"; \
    else \
        echo "No tools plugin found, skipping"; \
    fi && rm -rf /tmp/tools-plugin
```

After the deletion, the full Dockerfile should read:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install git (needed for openreview-py git dependency)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy and install MCP server
COPY pyproject.toml README.md ./
COPY openreview_mcp/ openreview_mcp/
RUN pip install --no-cache-dir .

# Knowledge files are bundled inside the package. To override with a live
# openreview-py clone, pass -e OPENREVIEW_KNOWLEDGE_PATH=/path at runtime.
ENTRYPOINT ["openreview-mcp"]
```

- [ ] **Step 3: Delete `build-docker.sh`**

```bash
git rm build-docker.sh
```

Expected: the file is removed. Its entire purpose was to `cp -r ../openreview-tools-mcp ./tools-plugin` before calling `docker build`. With the plugin hook gone, the wrapper is pure dead code and a plain `docker build -t openreview-mcp .` is the only invocation needed.

- [ ] **Step 4: Update `README.md` — remove the "with optional tools plugin" section**

Delete lines 12-17 of `README.md`:

```markdown
**With the optional tools plugin** (adds live API tools):
```bash
cp -r /path/to/openreview-tools-mcp /path/to/openreview-mcp/tools-plugin
docker build -t openreview-mcp /path/to/openreview-mcp
```
```

Also update line 38 which references the bind-mount-based knowledge path:

```markdown
The `-v` flag mounts your local openreview-py directory (which contains `llm.txt` and `examples.md`) into the container at `/knowledge`.
```

Replace with:

```markdown
Knowledge files (`llm.txt`, `examples.md`) are bundled inside the image — no bind-mount required. To override with a live openreview-py checkout, add `-e OPENREVIEW_KNOWLEDGE_PATH=/knowledge -v /path/to/openreview-py:/knowledge` to the `docker run` args.
```

Also update the `.mcp.json` snippet in the README (lines 23-36) to remove the now-unnecessary bind-mount:

```json
{
  "mcpServers": {
    "openreview": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "openreview-mcp"]
    }
  }
}
```

- [ ] **Step 5: Re-run the grep to confirm zero references remain**

```bash
grep -rn --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ "openreview[-_]tools" .
```

Expected: **no matches**. If any remain, track them down and delete them in this same commit.

- [ ] **Step 6: Run the full test suite (sanity check — nothing Python-side should have changed)**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 7: Build the Docker image to verify the simplified Dockerfile works end-to-end**

```bash
docker build -t openreview-mcp:decouple-test .
```

Expected: clean build, no "No tools plugin found, skipping" log line, no reference to `tools-plugin`.

- [ ] **Step 8: Smoke-test the Docker image by piping a list_tools request**

```bash
# FastMCP stdio servers respond to JSON-RPC. This is just a liveness check.
docker run --rm openreview-mcp:decouple-test --help 2>&1 | head -20 || true
```

Expected: the server starts (prints introspection log lines to stderr) and either blocks waiting for stdin input or exits after `--help`. Either way, no plugin-related errors.

- [ ] **Step 9: Commit**

```bash
git add Dockerfile README.md
git rm build-docker.sh
git commit -m "refactor: remove openreview-tools-mcp plugin hook

Flips the dependency direction: openreview-mcp is now strictly
knowledge-only with zero references to openreview-tools-mcp. The
downstream plan is for openreview-tools-mcp to depend on openreview-mcp
and mount its knowledge tools via register_knowledge_tools(mcp).

Removes:
- Dockerfile plugin install block (tools-plugi[n] glob trick)
- build-docker.sh wrapper (existed only to copy sibling plugin dir)
- README 'with optional tools plugin' quick-start variant
- README bind-mount-based knowledge path (bundled files make it unnecessary)

grep -r openreview[-_]tools now returns zero matches."
```

---

## Task 7: Finalize package metadata and refresh CLAUDE.md files

**Files:**
- Modify: `pyproject.toml:2` — name
- Modify: `pyproject.toml:3` — version
- Modify: `openreview_mcp/CLAUDE.md` — refresh for new module layout
- Modify: `tests/CLAUDE.md` — document new test files
- Modify: `CLAUDE.md` (repo root) — remove plugin references, update install story

- [ ] **Step 1: Update `pyproject.toml` package name and version**

Replace line 2:
```toml
name = "openreview-py-mcp"
```
with:
```toml
name = "openreview-mcp"
```

Replace line 3:
```toml
version = "0.1.0"
```
with:
```toml
version = "0.2.0"
```

Rationale for the rename: the distribution name now matches the repo name AND the importable package name, removing a three-way naming drift (`openreview-py-mcp` dist / `src` package / `openreview-mcp` repo). `0.2.0` reflects the breaking public API change.

- [ ] **Step 2: Reinstall to pick up the new distribution name**

```bash
.venv/bin/pip uninstall -y openreview-py-mcp openreview-mcp || true
.venv/bin/pip install -e ".[dev]"
```

Expected: installs as `openreview-mcp` version `0.2.0`. Verify:

```bash
.venv/bin/pip show openreview-mcp | grep -E "^(Name|Version):"
```

Expected output:
```
Name: openreview-mcp
Version: 0.2.0
```

- [ ] **Step 3: Rewrite `openreview_mcp/CLAUDE.md` to reflect the new module layout**

Replace the entire contents of `openreview_mcp/CLAUDE.md` with:

```markdown
# openreview_mcp/

FastMCP server implementation. Five modules: three data/logic modules, one reusable registration module, and a thin standalone entry point.

## Files

- `__init__.py` — Re-exports `register_knowledge_tools` as the package's public API. Zero import side effects.
- `registration.py` — Reusable `register_knowledge_tools(mcp, knowledge_path=None)` function. Builds the introspection cache and knowledge base at call time (not at import time), then defines the 5 tools as closures and registers them on the passed-in FastMCP instance. Returns a dict of tool name → tool handle for direct testing. Downstream consumers (e.g. `openreview-tools-mcp`) import this function and mount the knowledge tools onto their own FastMCP.
- `server.py` — Standalone entry point. Creates its own `FastMCP`, calls `register_knowledge_tools(mcp)`, provides `main()` for the `openreview-mcp` CLI script. ~30 lines total.
- `introspection.py` — Live introspection of the installed `openreview-py` package using Python's `inspect` module. `TARGET_CLASSES` lists the (module, class) pairs to introspect; `TARGET_MODULES` lists modules whose top-level functions are introspected as pseudo-classes. `search_methods()` ranks by exact name > name contains > docstring contains > param contains and caps results at 15. `get_method_details()` returns exact + partial name matches.
- `knowledge.py` — Parser for the static knowledge files. `KnowledgeBase` is a dataclass holding `practices` and `examples` as dicts keyed by `## ` section header.
- `knowledge_files/` — Bundled `llm.txt` and `examples.md`. These are the default knowledge source when `OPENREVIEW_KNOWLEDGE_PATH` is unset. Synced from `openreview-py` at release time.

## Important patterns

- `registration.py` has **zero import side effects**. No module-level `FastMCP`, no knowledge loading at import, no introspection at import. This is load-bearing: it lets downstream packages import `register_knowledge_tools` without accidentally spinning up a second server or blocking on `openreview-py` imports.
- `server.py` does the module-level work only because it IS the standalone entry point. Running `openreview-mcp` on the CLI is the only code path that creates a module-level FastMCP here.
- Tool functions return plain strings. LLMs consume the output directly, so keep formatting concise.
- `register_knowledge_tools` returns a dict `{tool_name: tool_handle}`. Each handle has a `.fn` attribute exposing the underlying function for direct testing. Production code ignores the return value.
- Knowledge path resolution priority: explicit `knowledge_path` arg > `OPENREVIEW_KNOWLEDGE_PATH` env var > bundled `knowledge_files/` directory.
- Environment variables: `OPENREVIEW_KNOWLEDGE_PATH` (optional override), `MCP_HOST`, `MCP_PORT`.

## When editing

- Adding a tool: add a new `@mcp.tool()`-decorated closure inside `register_knowledge_tools` and include it in the returned dict.
- Adding an introspection target: append to `TARGET_CLASSES` (classes) or `TARGET_MODULES` (top-level functions) in `introspection.py`. Private methods are skipped except `__init__`.
- Changing result formatting: update the `_format_*` helpers in `registration.py`.
- Updating bundled knowledge: `cp /Users/cmondragonch/Documents/openreview-py/llm.txt openreview_mcp/knowledge_files/` then same for `examples.md`. There is no auto-sync — this is a manual step at release time.
```

- [ ] **Step 4: Update `tests/CLAUDE.md` to list the new test files**

Edit the "## Files" section of `tests/CLAUDE.md`. Replace the existing bullets with:

```markdown
## Files

- `conftest.py` — Shared fixtures: `fixtures_dir`, `llm_txt_path`, `examples_md_path`. All resolve paths under `tests/fixtures/`.
- `test_introspection.py` — Unit tests for `openreview_mcp/introspection.py`. **Requires `openreview-py` installed** because it calls `introspect_library()` against the real package. Covers class discovery, method signature capture, docstring capture, private method skipping, and search ranking.
- `test_knowledge.py` — Unit tests for `openreview_mcp/knowledge.py`. Uses the fixture files in `tests/fixtures/` — **does not require** `openreview-py` installed.
- `test_bundled_knowledge.py` — Verifies that `llm.txt` and `examples.md` ship inside `openreview_mcp/knowledge_files/` and load without error. This is the regression test that catches a missed sync step at release time.
- `test_registration.py` — Tests `register_knowledge_tools`: asserts that all 5 tools land on a fresh FastMCP instance, that the function returns a dict of tool handles, and that invoking a handle via `.fn` hits real introspection data.
- `test_tools.py` — Behavior tests for the 5 tools. Uses a module-scoped `tools` fixture that creates a fresh FastMCP and calls `register_knowledge_tools(mcp)`, then invokes each tool via `tools["<name>"].fn(...)`.
- `fixtures/` — Fixture `llm.txt` and `examples.md`. See `tests/fixtures/CLAUDE.md`.
```

Then update the "## Running" section — `OPENREVIEW_KNOWLEDGE_PATH` is no longer required for the full suite because tests use bundled files:

```markdown
## Running

```bash
.venv/bin/python -m pytest tests/ -v
```

Tests pass without any environment variables — `test_tools.py`, `test_registration.py`, and `test_bundled_knowledge.py` all use the knowledge files bundled inside the package. Set `OPENREVIEW_KNOWLEDGE_PATH=/path/to/openreview-py` to override the bundled defaults if you're verifying against a live checkout.
```

- [ ] **Step 5: Update the repo-root `CLAUDE.md` "Helping Users Install" section**

In `CLAUDE.md` (repo root), the install walkthrough currently steps the user through locating `openreview-py` and setting `OPENREVIEW_KNOWLEDGE_PATH`. After bundling, that step is no longer required for a basic install. Edit the `### Step 5: Create .mcp.json` section's "not using conda" JSON example from:

```json
{
  "mcpServers": {
    "openreview": {
      "command": "openreview-mcp",
      "env": {
        "OPENREVIEW_KNOWLEDGE_PATH": "/path/to/openreview-py"
      }
    }
  }
}
```

to:

```json
{
  "mcpServers": {
    "openreview": {
      "command": "openreview-mcp"
    }
  }
}
```

And add a note below it:

```markdown
The `env` block is now optional — knowledge files are bundled inside the
package. Set `OPENREVIEW_KNOWLEDGE_PATH` only if you want to point at a
live `openreview-py` checkout for development.
```

Do the same edit to the conda-based JSON example.

- [ ] **Step 6: Run the full test suite one more time**

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected: all tests pass (documentation-only changes should not affect tests).

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml openreview_mcp/CLAUDE.md tests/CLAUDE.md CLAUDE.md
git commit -m "chore: finalize metadata and refresh CLAUDE.md files for v0.2.0

- Rename distribution from openreview-py-mcp to openreview-mcp so dist
  name, package name, and repo name all match.
- Bump version to 0.2.0 (breaking public API: tools are no longer
  module-level names on server.py).
- Refresh openreview_mcp/CLAUDE.md for the new registration.py split.
- Refresh tests/CLAUDE.md for test_registration.py and
  test_bundled_knowledge.py.
- Drop OPENREVIEW_KNOWLEDGE_PATH from the install walkthrough (bundled
  files make it optional)."
```

---

## Task 8: Release

**Files:**
- None modified — just verification + tagging

- [ ] **Step 1: Run the full test suite one final time with no env var**

```bash
unset OPENREVIEW_KNOWLEDGE_PATH
.venv/bin/python -m pytest tests/ -v
```

Expected: everything green.

- [ ] **Step 2: Build a fresh wheel and verify it bundles the knowledge files**

```bash
.venv/bin/pip install --upgrade build
.venv/bin/python -m build --wheel
.venv/bin/python -c "
import zipfile
import glob
wheel = glob.glob('dist/openreview_mcp-0.2.0-*.whl')[0]
with zipfile.ZipFile(wheel) as z:
    names = z.namelist()
    assert any('knowledge_files/llm.txt' in n for n in names), 'llm.txt missing from wheel'
    assert any('knowledge_files/examples.md' in n for n in names), 'examples.md missing from wheel'
    assert any('registration.py' in n for n in names), 'registration.py missing from wheel'
print('Wheel contents OK:')
print('\n'.join(n for n in names if 'openreview_mcp' in n))
"
```

Expected: the asserts pass and the printed listing shows `openreview_mcp/knowledge_files/llm.txt`, `openreview_mcp/knowledge_files/examples.md`, `openreview_mcp/registration.py`, `openreview_mcp/server.py`, etc.

- [ ] **Step 3: Verify the Docker image builds and runs without the knowledge bind-mount**

```bash
docker build -t openreview-mcp:0.2.0 .
docker run --rm openreview-mcp:0.2.0 2>&1 | head -20 &
DOCKER_PID=$!
sleep 2
kill $DOCKER_PID 2>/dev/null || true
wait 2>/dev/null || true
```

Expected: the container starts, the startup log shows `Introspected N classes, M methods total` and `Loaded N practice sections, M example sections` with non-zero counts, then the process is killed (no stdin piped in). No errors about missing knowledge files.

- [ ] **Step 4: Push the branch and merge to main**

```bash
cd /Users/cmondragonch/Documents/openreview-mcp-decouple
git log --oneline refactor/decouple-from-tools-mcp ^main
```

Expected output: a tidy sequence of 6-7 commits from this plan. Review each one before merging.

Then from the main worktree:

```bash
cd /Users/cmondragonch/Documents/openreview-mcp
git checkout main
git merge --no-ff refactor/decouple-from-tools-mcp -m "Merge refactor/decouple-from-tools-mcp

Refactor openreview-mcp into a publicly-distributable, knowledge-only
MCP server. Exposes register_knowledge_tools(mcp) so downstream
consumers (openreview-tools-mcp) can mount knowledge tools onto their
own FastMCP instance. Bundles llm.txt and examples.md inside the
package. Zero references to openreview-tools-mcp remain."
```

- [ ] **Step 5: Tag v0.2.0**

```bash
git tag -a v0.2.0 -m "v0.2.0 — decouple from openreview-tools-mcp

- Rename src/ to openreview_mcp/ for proper importable package name
- Extract register_knowledge_tools(mcp) in openreview_mcp/registration.py
- Bundle llm.txt and examples.md inside the package
- Remove openreview-tools-mcp plugin hook (Dockerfile, build-docker.sh, README)
- Rename distribution from openreview-py-mcp to openreview-mcp

This tag is what openreview-tools-mcp's pyproject.toml will pin via
'openreview-mcp @ git+https://github.com/openreview/openreview-mcp.git@v0.2.0'
in the follow-up plan."
```

- [ ] **Step 6: Confirm the tag is in place**

```bash
git tag -l "v0.2.0" --format='%(refname:strip=2) → %(contents:subject)'
```

Expected: `v0.2.0 → v0.2.0 — decouple from openreview-tools-mcp`

- [ ] **Step 7: Clean up the worktree**

```bash
git worktree remove /Users/cmondragonch/Documents/openreview-mcp-decouple
git branch -D refactor/decouple-from-tools-mcp
```

Expected: worktree directory gone, branch deleted locally (history preserved in main via the merge commit and the tag).

- [ ] **Step 8: Ask the user whether to push**

Stop here. Do not `git push` or `git push --tags` without explicit confirmation — pushing to `main` and publishing a tag are user-visible actions that should not happen automatically.

Prompt:
> "Local release complete: main is merged, v0.2.0 tagged. Ready to `git push origin main && git push origin v0.2.0` when you give the word."

---

## Out of scope (follow-up plan)

- Wiring `openreview-tools-mcp` to depend on `openreview-mcp@v0.2.0`.
- Creating a new standalone entry point in `openreview-tools-mcp` that imports `register_knowledge_tools` and `register_tools` onto the same FastMCP.
- Updating `openreview-tools-mcp/pyproject.toml`, its Dockerfile, and its README.
- Verifying the combined server exposes 11 tools (5 knowledge + 6 live API).

Those land in `docs/superpowers/plans/2026-04-XX-wire-tools-mcp-to-knowledge.md` (to be written after this plan merges).
