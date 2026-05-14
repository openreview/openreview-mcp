# OpenReview Python MCP Server

MCP server that helps LLMs write correct `openreview-py` code. Two knowledge layers: **live introspection** of the installed library (method signatures, docstrings, class structures) and **static knowledge** (best practices, code examples, workflow guides).

## Tools

| Tool | Purpose |
|------|---------|
| `search_api` | Search OpenReview API methods by topic (results tagged `[v1]`/`[v2]`) |
| `get_method_signature` | Get detailed method signatures and docstrings |
| `get_best_practices` | Concepts, conventions, and anti-patterns from `best_practices.md` (curated in this repo) |
| `search_test_examples` | Real call sites from the upstream `openreview-py/tests/` directory (auto-indexed) |

## Usage

### Quick start (recommended)

Clone, build, and run as a long-running local HTTP service. This is the path teammates should use — it survives Claude Code restarts and the `openreview-py` mount lights up live introspection **and** the test-suite index (`search_test_examples`).

```bash
git clone https://github.com/openreview/openreview-mcp.git
cd openreview-mcp
docker build -t openreview-mcp .

# Adjust the path to your local openreview-py checkout
docker run -d --name openreview-mcp -p 8080:8080 \
  -v /path/to/openreview-py:/knowledge \
  -e OPENREVIEW_KNOWLEDGE_PATH=/knowledge \
  openreview-mcp --transport streamable-http
```

Add to `.mcp.json` (project-level) **or** to `~/.claude.json` under the relevant project's `mcpServers`:

```json
{
  "mcpServers": {
    "openreview": {
      "type": "http",
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

Restart Claude Code (`/exit` and relaunch). All 4 tools become available; `search_test_examples` will index your live `openreview-py/tests/` directory at container start.

**To upgrade later:**

```bash
git pull && docker build --no-cache -t openreview-mcp .
docker stop openreview-mcp && docker rm openreview-mcp
docker run -d --name openreview-mcp -p 8080:8080 \
  -v /path/to/openreview-py:/knowledge \
  -e OPENREVIEW_KNOWLEDGE_PATH=/knowledge \
  openreview-mcp --transport streamable-http
```

`--no-cache` ensures pip refetches the latest `openreview-py` from GitHub instead of using a cached layer.

### Alternative: stdio per-call (no long-running service)

If you'd rather Claude Code spawn a fresh container on every tool call (lower idle footprint, but introspection + index rebuild on each invocation):

```json
{
  "mcpServers": {
    "openreview": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/path/to/openreview-py:/knowledge",
        "-e", "OPENREVIEW_KNOWLEDGE_PATH=/knowledge",
        "openreview-mcp"
      ]
    }
  }
}
```

### Without an openreview-py checkout

If you don't have `openreview-py` cloned locally, drop the `-v` and `-e` flags. The bundled `best_practices.md` and the openreview-py git dependency installed inside the image still power `search_api`, `get_method_signature`, and `get_best_practices`. `search_test_examples` will return a disabled message until you mount a `tests/` directory.

### Remote server (public, optional)

Deploy the same image to any host that can run Docker (Cloud Run, Fly.io, a VM, etc.) and point clients at its public URL:

```json
{
  "mcpServers": {
    "openreview": {
      "type": "http",
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

### Environment variables

| Var | Purpose |
|-----|---------|
| `OPENREVIEW_KNOWLEDGE_PATH` | Optional directory hint. If it contains a `best_practices.md`, that file is loaded instead of the bundled one (otherwise the bundled copy is used — no error). If it also contains a `tests/` subdir (as the `openreview-py` repo does), the test-suite index auto-enables. |
| `OPENREVIEW_TESTS_PATH` | Explicit override for the `tests/` directory used by `search_test_examples`. Falls back to `{OPENREVIEW_KNOWLEDGE_PATH}/tests/`. |

## Reusable Registration

Other FastMCP servers can mount the knowledge tools without running the full server:

```python
from openreview_mcp.registration import register_knowledge_tools

register_knowledge_tools(mcp)  # mounts 5 knowledge tools onto your FastMCP instance
```

## Keeping Up with openreview-py

The server has three layers, each with a different freshness story:

- **Introspection** (`search_api`, `get_method_signature`) — reads the installed `openreview-py` at startup. Refreshes when you rebuild the image (`--no-cache` forces pip to refetch) or when you mount a live checkout via `OPENREVIEW_KNOWLEDGE_PATH` (introspects from inside the container's editable install path).
- **Static knowledge** (`get_best_practices`) — reads `best_practices.md` (concepts, conventions, anti-patterns; the rules tests assert but never explain). Curated and edited in this repo; bundled inside the image. Refresh by editing the file in `openreview_mcp/knowledge_files/` and rebuilding (or mounting your own copy via `OPENREVIEW_KNOWLEDGE_PATH`).
- **Test-suite index** (`search_test_examples`) — AST-indexed at startup from the `tests/` subdir of whatever `OPENREVIEW_KNOWLEDGE_PATH` (or `OPENREVIEW_TESTS_PATH`) points at. Always reflects the working tree of the mounted checkout — `git pull` in your `openreview-py` checkout and restart the container.

## Development

```bash
git clone https://github.com/openreview/openreview-mcp.git
cd openreview-mcp
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v
```
