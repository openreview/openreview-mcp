# OpenReview Python MCP Server

MCP server that helps LLMs write correct `openreview-py` code. Two knowledge layers: **live introspection** of the installed library (method signatures, docstrings, class structures) and **static knowledge** (best practices, code examples, workflow guides).

## Tools

| Tool | Purpose |
|------|---------|
| `search_api` | Search OpenReview API methods by topic |
| `get_method_signature` | Get detailed method signatures and docstrings |
| `get_best_practices` | Find best practices and patterns |
| `get_code_example` | Retrieve code examples for common operations |
| `get_workflow_guide` | Get step-by-step workflow guides |

## Quick Start

### 1. Build the Docker image

```bash
docker build -t openreview-mcp .
```

### 2. Add to Claude Code

Create a `.mcp.json` file in the root of the project you're working in (or in `~/.claude/` for global access):

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

Knowledge files (`llm.txt`, `examples.md`) are bundled inside the image — no bind-mount required. To override with a live openreview-py checkout, add `-e OPENREVIEW_KNOWLEDGE_PATH=/knowledge -v /path/to/openreview-py:/knowledge` to the `docker run` args.

### 3. Restart and verify

Restart Claude Code (`/exit` and relaunch). The 5 tools will be available immediately.

## Reusable Registration

Other FastMCP servers can mount the knowledge tools without running the full server:

```python
from openreview_mcp.registration import register_knowledge_tools

register_knowledge_tools(mcp)  # mounts 5 knowledge tools onto your FastMCP instance
```

## Development

```bash
git clone https://github.com/openreview/openreview-mcp.git
cd openreview-mcp
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v
```
