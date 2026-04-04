# OpenReview Python MCP Server

MCP server that helps LLMs write correct `openreview-py` code. Two knowledge layers: **live introspection** of the installed library (method signatures, docstrings, class structures) and **static knowledge** (best practices, code examples, workflow guides).

## Quick Start

### Prerequisites

- Python 3.11+
- A local clone of [openreview-py](https://github.com/openreview/openreview-py)
- `pip` (or `uv` if you prefer)

### 1. Install openreview-py (editable)

The MCP server introspects openreview-py at runtime to read its docstrings. Install it as an editable package so the server always sees the latest code:

```bash
pip install -e /path/to/openreview-py
```

### 2. Install the MCP server

```bash
pip install -e /path/to/openreview-mcp
```

### 3. Verify it works

```bash
openreview-mcp
```

You should see the FastMCP startup banner. Press `Ctrl+C` to stop.

### 4. Add to Claude Code

Create a `.mcp.json` file in the root of the project you're working in (or in `~/.claude/` for global access):

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

Then restart Claude Code. The 5 tools will be available immediately.

> **Note:** If you installed into a conda environment, use the full path to the binary:
> ```json
> {
>   "mcpServers": {
>     "openreview": {
>       "command": "/path/to/conda/envs/yourenv/bin/openreview-mcp",
>       "env": {
>         "OPENREVIEW_KNOWLEDGE_PATH": "/path/to/openreview-py"
>       }
>     }
>   }
> }
> ```
> Find the path with: `conda run -n yourenv which openreview-mcp`

### 5. Add to Cursor

Go to **Cursor Settings > MCP** and add a new server:

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

## Tools

### `search_api`
Search openreview-py methods and classes by keyword. Supports multi-word queries (all words must match).

- `query` (required): Search term (e.g., "edge", "post note", "assign reviewers", "review stage")
- `class_name` (optional): Filter to a specific class (e.g., "OpenReviewClient", "Venue", "Journal")

### `get_method_signature`
Get full details for a specific method — signature, parameters, docstring.

- `method_name` (required): Exact or partial name (e.g., "post_note_edit", "setup_committee_matching")

### `get_best_practices`
Get best practices and rules for a topic from the knowledge base.

- `topic` (required): Topic keyword (e.g., "authentication", "permissions", "anti-patterns")

### `get_code_example`
Get clean, minimal code examples for an operation.

- `operation` (required): What you want to do (e.g., "submit paper", "post edge", "recruit reviewers")

### `get_workflow_guide`
Get step-by-step workflow guide with code examples.

- `workflow_type` (required): "conference", "journal", or a stage name like "matching", "review", "decision"

## Introspected Classes

The server introspects these classes at startup and indexes their public methods:

| Class | Module | Description |
|-------|--------|-------------|
| `OpenReviewClient` | `openreview.api.client` | V2 API client — primary interface |
| `Client` | `openreview.openreview` | V1 API client |
| `Note` | `openreview.api.client` | Submission/review/decision data model |
| `Invitation` | `openreview.api.client` | Permission and schema definitions |
| `Edge` | `openreview.api.client` | Relationships (assignments, bids, scores) |
| `Group` | `openreview.api.client` | User/role groups |
| `Tag` | `openreview.api.client` | Lightweight annotations |
| `Edit` | `openreview.api.client` | V2 edit wrapper for Notes/Groups/Invitations |
| `Profile` | `openreview.openreview` | User profiles |
| `Venue` | `openreview.venue` | High-level conference management |
| `Journal` | `openreview.journal` | High-level journal management |

Adding or improving docstrings in openreview-py is automatically picked up on server restart.

## Architecture

```
openreview-mcp/
├── src/
│   ├── server.py           # FastMCP server + 5 tool definitions
│   ├── introspection.py    # Live introspection via Python inspect module
│   ├── knowledge.py        # Static knowledge parser (llm.txt + examples.md)
│   └── __init__.py
├── tests/
│   ├── test_introspection.py
│   ├── test_knowledge.py
│   ├── test_tools.py
│   ├── conftest.py
│   └── fixtures/
├── pyproject.toml
└── CLAUDE.md
```

**Live introspection layer**: imports `openreview` at startup, uses `inspect` module to extract signatures and docstrings from 11 classes. Search ranks results by: exact name match > name contains > docstring contains > param contains.

**Static knowledge layer**: reads `llm.txt` (best practices, constraints, anti-patterns) and `examples.md` (code snippets) from a configurable path. Parsed into indexed sections for keyword search.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENREVIEW_KNOWLEDGE_PATH` | `../../openreview-py` relative to src/ | Path to directory containing `llm.txt` and `examples.md` |

## Development

```bash
# Run tests
OPENREVIEW_KNOWLEDGE_PATH=/path/to/openreview-py pytest tests/ -v

# Format
black .

# Lint
ruff check .
```
