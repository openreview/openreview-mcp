Project Overview & Context:
This project is an MCP server built with FastMCP that helps LLMs write correct openreview-py code. It provides three knowledge layers: live introspection of the installed openreview-py library (method signatures, docstrings, class structures); a curated `best_practices.md` of concepts, conventions, and anti-patterns (maintained in this repo, not synced from upstream); and an AST-postings index over the upstream `openreview-py/tests/` directory for real call sites. The server exposes 4 tools. Built with Python 3.11+.

Project Structure:
```
openreview-mcp/
├── openreview_mcp/
│   ├── __init__.py             # Re-exports register_knowledge_tools
│   ├── registration.py         # Reusable register_knowledge_tools(mcp) — zero import side effects
│   ├── server.py               # Thin FastMCP standalone entry point
│   ├── introspection.py        # Live introspection via inspect module
│   ├── knowledge.py            # Static knowledge parser (best_practices.md)
│   ├── tests_index.py          # AST-postings index over upstream openreview-py tests
│   └── knowledge_files/
│       └── best_practices.md   # Curated concepts/conventions/anti-patterns (edited in this repo)
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── test_introspection.py   # Layer 1: introspection unit tests
│   ├── test_knowledge.py       # Layer 2: knowledge parsing unit tests
│   ├── test_tests_index.py     # Layer 3: tests-index unit tests (hermetic fixtures)
│   ├── test_bundled_knowledge.py  # Release-time bundling regression guard
│   ├── test_registration.py    # Tests for register_knowledge_tools
│   ├── test_tools.py           # Tool behavior via FastMCP fixture
│   └── fixtures/
│       └── fake_tests/         # Synthetic test files for the tests-index fixture
├── Dockerfile
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

Key files: `openreview_mcp/registration.py` (the reusable `register_knowledge_tools` function that defines the tools as closures), `openreview_mcp/server.py` (thin standalone entry point), `openreview_mcp/introspection.py` (live introspection), `openreview_mcp/knowledge.py` (static knowledge parser), `openreview_mcp/tests_index.py` (AST-postings index over upstream openreview-py tests, lazy body read via linecache).

Public API:
- `from openreview_mcp import register_knowledge_tools` — mounts the 5 knowledge tools onto any FastMCP instance. Zero import side effects (introspection and knowledge loading happen at call time, not import). Returns a `dict[str, Callable[..., str]]` of tool handles keyed by name. Downstream consumers can import and use this to combine the knowledge tools with their own MCP tools on a single server.

Environment Variables:
- `OPENREVIEW_KNOWLEDGE_PATH` (optional): directory hint. **The Docker image sets this to `/openreview-py` by default**, pointing at the baked-in shallow clone of upstream `openreview-py`, so `search_test_examples` works out of the box. If the resolved directory contains a `best_practices.md`, that file is loaded instead of the bundled one (otherwise the bundled copy is used — no error). If it also contains a `tests/` subdir, the test-suite index uses it. The bundled `best_practices.md` is the source of truth — it is edited in this repo and not synced from upstream.
- `OPENREVIEW_TESTS_PATH` (optional): explicit path to an `openreview-py/tests/` directory for the `search_test_examples` tool. If unset, falls back to `{OPENREVIEW_KNOWLEDGE_PATH}/tests/` when it exists. If still unresolved, `search_test_examples` returns a clear disabled message and the other tools work unaffected.

Tools (4 total):
1. `search_api(query, class_name?)` — Search methods/classes by keyword with relevance ranking; results tagged `[v1]` / `[v2]`
2. `get_method_signature(method_name)` — Full details for a specific method (includes `**API:**` v1/v2 marker)
3. `get_best_practices(topic)` — Concepts, conventions, and anti-patterns from `best_practices.md` (curated in this repo)
4. `search_test_examples(query, max_results=5)` — Real call sites from the upstream openreview-py test suite (auto-current; AST-indexed at registration time)

Code Style & Conventions:
- snake_case for files and functions, PascalCase for classes
- Docstrings on all public functions
- Avoid redundant information in tool output — LLMs need concise, non-repetitive context
- Use decorators (`@mcp.tool()`) to register tools
- Tool closures live inside `register_knowledge_tools` to keep side effects at call-time

Running Tests:
```bash
.venv/bin/python -m pytest tests/ -v
```

No environment variables required — tests use the bundled `best_practices.md` and the hermetic fixtures in `tests/fixtures/`.

---

## Helping Users Install the MCP Server

When a user asks for help installing or setting up this MCP server, walk them through these steps interactively. Run the commands for them when possible, ask for confirmation on paths.

### Step 1: Locate openreview-py

Ask the user where their openreview-py clone is. Common locations:
- `~/Documents/openreview-py`
- `~/projects/openreview-py`
- A sibling directory to this repo

Verify it exists:
```bash
ls /path/to/openreview-py/openreview/__init__.py
```

### Step 2: Detect Python environment

Check if the user has a conda env or virtualenv with openreview-py installed:
```bash
# Check for conda env
conda env list 2>/dev/null | grep openreview
# Or check for a virtualenv
which python3
pip show openreview-py
```

### Step 3: Install openreview-py as editable

This is critical — the MCP server introspects docstrings from the installed openreview-py. It must be the local clone (editable), not the pip/GitHub version:
```bash
pip install -e /path/to/openreview-py
```

Verify the editable install:
```bash
pip show openreview-py | grep "Editable project location"
```
This MUST show the local path. If it doesn't, the MCP server will serve stale/empty docstrings.

### Step 4: Install the MCP server

```bash
pip install -e /path/to/openreview-mcp
```

Verify:
```bash
which openreview-mcp
```

### Step 5: Create .mcp.json

Create a `.mcp.json` file in the root of the project the user works in (usually openreview-py):

If using conda, get the full binary path first:
```bash
conda run -n ENVNAME which openreview-mcp
```

Then create `.mcp.json`:
```json
{
  "mcpServers": {
    "openreview": {
      "command": "/full/path/to/bin/openreview-mcp"
    }
  }
}
```

If not using conda (plain pip install), the simpler form works:
```json
{
  "mcpServers": {
    "openreview": {
      "command": "openreview-mcp"
    }
  }
}
```

The `best_practices.md` knowledge file is bundled inside the package, and the Docker image bakes in a shallow clone of `openreview-py` at `/openreview-py` (with `OPENREVIEW_KNOWLEDGE_PATH` pre-set to that path), so no `env` block is required for a basic setup — all 4 tools work out of the box. To pick up live edits to a local `openreview-py` checkout instead of the baked-in clone, bind-mount it at `/openreview-py` (Docker) or override `OPENREVIEW_KNOWLEDGE_PATH` (non-Docker / pip-install path):
```json
"env": {
  "OPENREVIEW_KNOWLEDGE_PATH": "/path/to/openreview-py"
}
```

Note: `.mcp.json` is gitignored (contains machine-specific absolute paths). Each developer creates their own.

### Step 6: Restart Claude Code

Tell the user to restart Claude Code (`/exit` and relaunch) for it to pick up the new `.mcp.json`. After restart, the 5 openreview MCP tools will be available.

### Step 7: Verify

After restart, test that the tools work:
- Search: `search_api("post note")` should return results
- Signatures: `get_method_signature("post_note_edit")` should return a full docstring

If `get_method_signature` returns an empty docstring, the editable install in Step 3 likely failed — re-check with `pip show openreview-py`.
