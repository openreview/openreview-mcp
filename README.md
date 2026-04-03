# OpenReview Python MCP Server

MCP server that helps LLMs write correct `openreview-py` code. Two knowledge layers: **live introspection** of the installed library (method signatures, docstrings, class structures) and **static knowledge** (best practices, code examples, workflow guides).

## Quick Start

### Prerequisites

- Python 3.11+
- `uv` package manager

### Installation

```bash
cd openreview-mcp
uv sync
```

### Running

```bash
# Set path to llm.txt and examples.md
export OPENREVIEW_KNOWLEDGE_PATH=/path/to/openreview-py

# Run the server
uv run openreview-mcp
```

### Claude Code Configuration

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "openreview": {
      "command": "uv",
      "args": ["run", "python", "/path/to/openreview-mcp/src/server.py"],
      "env": {
        "OPENREVIEW_KNOWLEDGE_PATH": "/path/to/openreview-py"
      }
    }
  }
}
```

## Tools

### `search_api`
Search openreview-py methods and classes by keyword.

- `query` (required): Search term (e.g., "edge", "post note", "profile merge")
- `class_name` (optional): Filter to a specific class (e.g., "OpenReviewClient", "Venue")

### `get_method_signature`
Get full details for a specific method — signature, parameters, docstring.

- `method_name` (required): Exact or partial name (e.g., "post_note_edit", "get_all_notes")

### `get_best_practices`
Get best practices and rules for a topic from the knowledge base.

- `topic` (required): Topic keyword (e.g., "authentication", "permissions", "anti-patterns")

### `get_code_example`
Get clean, minimal code examples for an operation.

- `operation` (required): What you want to do (e.g., "submit paper", "post edge", "recruit reviewers")

### `get_workflow_guide`
Get step-by-step workflow guide with code examples.

- `workflow_type` (required): "conference", "journal", or a stage name like "matching", "review", "decision"

## Architecture

```
openreview-mcp/
├── src/
│   ├── server.py           # FastMCP server + 5 tool definitions
│   ├── introspection.py    # Live introspection via Python inspect module
│   ├── knowledge.py        # Static knowledge parser (llm.txt + examples.md)
│   └── __init__.py
├── tests/
│   ├── test_introspection.py  # 14 tests: library introspection
│   ├── test_knowledge.py      # 13 tests: knowledge parsing
│   ├── test_tools.py          # 7 tests: MCP tool integration
│   ├── conftest.py
│   └── fixtures/
├── pyproject.toml
└── CLAUDE.md
```

**Live introspection layer**: imports `openreview` at startup, uses `inspect` module to extract signatures and docstrings from 10 classes (OpenReviewClient, Note, Invitation, Edge, Group, Tag, Edit, Profile, Client, Venue). Adding docstrings to openreview-py is automatically picked up on restart.

**Static knowledge layer**: reads `llm.txt` (best practices, constraints, anti-patterns) and `examples.md` (code snippets) from a configurable path. Parsed into indexed sections for keyword search.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `OPENREVIEW_KNOWLEDGE_PATH` | `../../openreview-py` relative to src/ | Path to directory containing `llm.txt` and `examples.md` |
| `MCP_HOST` | `localhost` | Server host |
| `MCP_PORT` | `4000` | Server port |

## Development

```bash
# Run tests
OPENREVIEW_KNOWLEDGE_PATH=/path/to/openreview-py .venv/bin/python -m pytest tests/ -v

# Format
uv run black .

# Lint
uv run ruff check .
```
