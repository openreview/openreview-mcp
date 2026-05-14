Project Overview & Context:
This project is an MCP server built with FastMCP that helps LLMs write correct openreview-py code. It provides two knowledge layers: live introspection of the installed openreview-py library (method signatures, docstrings, class structures) and static knowledge files (best practices, code examples, workflow guides — bundled inside the package). The server exposes 5 tools that LLM clients use to find API methods, understand best practices, get code examples, and follow workflow patterns. Built with Python 3.11+.

Project Structure:
```
openreview-mcp/
├── openreview_mcp/
│   ├── __init__.py             # Re-exports register_knowledge_tools
│   ├── registration.py         # Reusable register_knowledge_tools(mcp) — zero import side effects
│   ├── server.py               # Thin FastMCP standalone entry point
│   ├── introspection.py        # Live introspection via inspect module
│   ├── knowledge.py            # Static knowledge parser (llm.txt + examples.md)
│   ├── tests_index.py          # AST-postings index over upstream openreview-py tests
│   └── knowledge_files/
│       ├── llm.txt             # Bundled best-practices source
│       └── examples.md         # Bundled code-examples source
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
├── docs/
│   ├── DEPLOYMENT.md
│   └── superpowers/            # Specs and plans
├── Dockerfile
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

Key files: `openreview_mcp/registration.py` (the reusable `register_knowledge_tools` function that defines the tools as closures), `openreview_mcp/server.py` (thin standalone entry point), `openreview_mcp/introspection.py` (live introspection), `openreview_mcp/knowledge.py` (static knowledge parser), `openreview_mcp/tests_index.py` (AST-postings index over upstream openreview-py tests, lazy body read via linecache).

Public API:
- `from openreview_mcp import register_knowledge_tools` — mounts the 5 knowledge tools onto any FastMCP instance. Zero import side effects (introspection and knowledge loading happen at call time, not import). Returns a `dict[str, Callable[..., str]]` of tool handles keyed by name. Downstream consumers can import and use this to combine the knowledge tools with their own MCP tools on a single server.

Environment Variables:
- `OPENREVIEW_KNOWLEDGE_PATH` (optional): path to a directory containing `llm.txt` and `examples.md`. Defaults to the bundled `openreview_mcp/knowledge_files/` directory. Set this to override with a live openreview-py checkout during development. If this path also contains a `tests/` subdir (as the openreview-py repo does), the test-suite index auto-enables.
- `OPENREVIEW_TESTS_PATH` (optional): explicit path to an `openreview-py/tests/` directory for the `search_test_examples` tool. If unset, falls back to `{OPENREVIEW_KNOWLEDGE_PATH}/tests/` when it exists. If still unresolved, `search_test_examples` returns a clear disabled message and the other tools work unaffected.

Tools (6 total):
1. `search_api(query, class_name?)` — Search methods/classes by keyword with relevance ranking
2. `get_method_signature(method_name)` — Full details for a specific method
3. `get_best_practices(topic)` — Best practices from llm.txt by topic
4. `get_code_example(operation)` — Code examples from examples.md
5. `get_workflow_guide(workflow_type)` — Step-by-step workflow guides with code
6. `search_test_examples(query, max_results=5)` — Real call sites from the upstream openreview-py test suite (auto-current; AST-indexed at registration time)

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

No environment variables required — tests use the bundled knowledge files. Set `OPENREVIEW_KNOWLEDGE_PATH=/path/to/openreview-py` only if you want to verify against a live upstream checkout.

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

Knowledge files (`llm.txt`, `examples.md`) are bundled inside the package, so no `env` block is required for a basic setup. If the user wants to point at a live `openreview-py` checkout for development (so edits to `llm.txt` / `examples.md` upstream are picked up without re-syncing), add an `env` block:
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
