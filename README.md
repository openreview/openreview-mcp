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

Clone, build, and run as a long-running local HTTP service. The image bakes in a shallow clone of `openreview-py` so all 4 tools — including `search_test_examples` — work out of the box; no host bind-mount required.

```bash
git clone https://github.com/openreview/openreview-mcp.git
cd openreview-mcp
docker build -t openreview-mcp .

docker run -d --name openreview-mcp -p 8080:8080 \
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

Restart Claude Code (`/exit` and relaunch). All 4 tools become available; `search_test_examples` indexes the `openreview-py/tests/` directory baked into the image at container start.

**To upgrade later** (picks up new `openreview-mcp` code, new upstream `openreview-py`, and new tests):

```bash
git pull && docker build --no-cache -t openreview-mcp .
docker stop openreview-mcp && docker rm openreview-mcp
docker run -d --name openreview-mcp -p 8080:8080 \
  openreview-mcp --transport streamable-http
```

`--no-cache` is what forces both the pip-installed `openreview-py` and the cloned tests directory to refresh to the latest upstream `main`.

### Use a local `openreview-py` checkout

If you're editing `openreview-py` and want the MCP to reflect your working tree (live introspection + tests-index against your branch), bind-mount it on top of the baked-in clone:

```bash
docker run -d --name openreview-mcp -p 8080:8080 \
  -v /path/to/your/openreview-py:/openreview-py \
  openreview-mcp --transport streamable-http
```

No env var needed — the image already sets `OPENREVIEW_KNOWLEDGE_PATH=/openreview-py`, so the bind mount transparently replaces the baked-in clone.

### Alternative: stdio per-call (no long-running service)

If you'd rather Claude Code spawn a fresh container on every tool call (lower idle footprint, but introspection + index rebuild on each invocation):

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
| `OPENREVIEW_KNOWLEDGE_PATH` | Directory hint for `search_test_examples` and (optionally) for an override `best_practices.md`. The Dockerfile sets this to `/openreview-py` (the baked-in clone) by default. If it contains a `best_practices.md`, that file is loaded instead of the bundled one (otherwise the bundled copy is used — no error). The `tests/` subdir under this path is what `search_test_examples` indexes. |
| `OPENREVIEW_TESTS_PATH` | Explicit override for the `tests/` directory used by `search_test_examples`. Falls back to `{OPENREVIEW_KNOWLEDGE_PATH}/tests/`. |

## Reusable Registration

Other FastMCP servers can mount the knowledge tools without running the full server:

```python
from openreview_mcp.registration import register_knowledge_tools

register_knowledge_tools(mcp)  # mounts 4 knowledge tools onto your FastMCP instance
```

## Keeping Up with openreview-py

The server has three layers, each with a different freshness story:

- **Introspection** (`search_api`, `get_method_signature`) — reads the installed `openreview-py` at startup. Refreshes when you rebuild the image; `--no-cache` forces pip to refetch upstream `main`.
- **Static knowledge** (`get_best_practices`) — reads `best_practices.md` (concepts, conventions, anti-patterns; the rules tests assert but never explain). Curated and edited in this repo; bundled inside the image. Refresh by editing `openreview_mcp/knowledge_files/best_practices.md` and rebuilding.
- **Test-suite index** (`search_test_examples`) — AST-indexed at startup from the `openreview-py/tests/` directory that the Dockerfile clones into `/openreview-py`. Refresh by rebuilding with `--no-cache` (forces the clone layer to re-fetch), or bind-mount your own checkout at `/openreview-py` for live-edit workflows.

## Development

```bash
git clone https://github.com/openreview/openreview-mcp.git
cd openreview-mcp
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v
```
