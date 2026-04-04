Project Overview & Context:
This project is an MCP server built with FastMCP that helps LLMs write correct openreview-py code. It provides two knowledge layers: live introspection of the installed openreview-py library (method signatures, docstrings, class structures) and static knowledge files (best practices, code examples, workflow guides). The server exposes 5 tools that LLM clients use to find API methods, understand best practices, get code examples, and follow workflow patterns. Built with Python 3.11+ and uv package manager.

Project Structure:
```
openreview-mcp/
├── src/
│   ├── server.py           # FastMCP server + 5 tool definitions
│   ├── introspection.py    # Live introspection of openreview-py via inspect module
│   ├── knowledge.py        # Static knowledge parser (llm.txt + examples.md)
│   └── __init__.py
├── tests/
│   ├── test_introspection.py  # Layer 1: introspection unit tests
│   ├── test_knowledge.py      # Layer 2: knowledge parsing unit tests
│   ├── test_tools.py          # Layer 3: MCP tool integration tests
│   ├── conftest.py            # Shared fixtures
│   └── fixtures/              # Test fixture files
├── docs/
│   ├── DEPLOYMENT.md
│   └── superpowers/specs/     # Design specs
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

Key files: `src/server.py` (tool definitions), `src/introspection.py` (live introspection), `src/knowledge.py` (static knowledge).

Environment Variables:
- `OPENREVIEW_KNOWLEDGE_PATH`: path to directory containing `llm.txt` and `examples.md` (defaults to `../../openreview-py` relative to src/)

Tools (5 total):
1. `search_api(query, class_name?)` — Search methods/classes by keyword with relevance ranking
2. `get_method_signature(method_name)` — Full details for a specific method
3. `get_best_practices(topic)` — Best practices from llm.txt by topic
4. `get_code_example(operation)` — Code examples from examples.md
5. `get_workflow_guide(workflow_type)` — Step-by-step workflow guides with code

Code Style & Conventions:
- snake_case for files and functions, PascalCase for classes
- Docstrings on all public functions
- Avoid redundant information in tool output — LLMs need concise, non-repetitive context
- Use decorators (`@mcp.tool()`) to register tools

Running Tests:
```bash
OPENREVIEW_KNOWLEDGE_PATH=/path/to/openreview-py .venv/bin/python -m pytest tests/ -v
```

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
      "command": "/full/path/to/bin/openreview-mcp",
      "env": {
        "OPENREVIEW_KNOWLEDGE_PATH": "/path/to/openreview-py"
      }
    }
  }
}
```

If not using conda (plain pip install), the simpler form works:
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

Note: `.mcp.json` is gitignored (contains machine-specific absolute paths). Each developer creates their own.

### Step 6: Restart Claude Code

Tell the user to restart Claude Code (`/exit` and relaunch) for it to pick up the new `.mcp.json`. After restart, the 5 openreview MCP tools will be available.

### Step 7: Verify

After restart, test that the tools work:
- Search: `search_api("post note")` should return results
- Signatures: `get_method_signature("post_note_edit")` should return a full docstring

If `get_method_signature` returns an empty docstring, the editable install in Step 3 likely failed — re-check with `pip show openreview-py`.
