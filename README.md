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

## Usage

### Option 1: Local Docker (stdio)

Build and use directly with Claude Code:

```bash
docker build -t openreview-mcp .
```

Add to `.mcp.json`:

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

Restart Claude Code (`/exit` and relaunch). The 5 tools will be available immediately.

### Option 2: Local Docker service (SSE)

Run as a persistent local service:

```bash
docker run -d --name openreview-mcp -p 8080:8080 openreview-mcp --transport sse
```

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "openreview": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

### Option 3: Remote server (public)

Deploy to any host that can run Docker (Cloud Run, Fly.io, a VM, etc.):

```bash
docker run -d -p 8080:8080 openreview-mcp --transport streamable-http
```

Clients connect via `.mcp.json`:

```json
{
  "mcpServers": {
    "openreview": {
      "url": "https://your-server.example.com/mcp"
    }
  }
}
```

No API token is needed — this server provides knowledge tools only (read-only, no live API access).

### CLI options

```
openreview-mcp [--transport stdio|sse|streamable-http] [--port 8080] [--host 0.0.0.0]
```

Knowledge files (`llm.txt`, `examples.md`) are bundled inside the image — no bind-mount required. To override with a live openreview-py checkout, add `-e OPENREVIEW_KNOWLEDGE_PATH=/knowledge -v /path/to/openreview-py:/knowledge` to the `docker run` args.

## Reusable Registration

Other FastMCP servers can mount the knowledge tools without running the full server:

```python
from openreview_mcp.registration import register_knowledge_tools

register_knowledge_tools(mcp)  # mounts 5 knowledge tools onto your FastMCP instance
```

## Keeping Up with openreview-py

The introspection layer (`search_api`, `get_method_signature`) reads directly from the installed `openreview-py` library at startup. When `openreview-py` adds or changes methods, rebuild the Docker image to pick them up:

```bash
docker build --no-cache -t openreview-mcp .
```

The `--no-cache` flag ensures pip fetches the latest `openreview-py` from GitHub instead of using a cached layer.

For the static knowledge layer (`get_best_practices`, `get_code_example`, `get_workflow_guide`), update the bundled files in `openreview_mcp/knowledge_files/` and rebuild.

Alternatively, to use a live checkout of `openreview-py` without rebuilding, mount it at runtime:

```bash
docker run --rm -i \
  -e OPENREVIEW_KNOWLEDGE_PATH=/knowledge \
  -v /path/to/openreview-py:/knowledge \
  openreview-mcp
```

This overrides both the introspected library and the knowledge files path.

## Development

```bash
git clone https://github.com/openreview/openreview-mcp.git
cd openreview-mcp
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v
```
