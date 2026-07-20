# OpenReview Python MCP Server

MCP server that helps LLMs write correct `openreview-py` code. Two knowledge layers: **live introspection** of the installed library (method signatures, docstrings, class structures) and a **test-suite index** over the upstream `openreview-py/tests/` directory (real call sites).

## Tools

| Tool | Purpose |
|------|---------|
| `search_api` | Search OpenReview API methods by topic (results tagged `[v1]`/`[v2]`) |
| `get_method_signature` | Get detailed method signatures and docstrings |
| `search_test_examples` | Real call sites from the upstream `openreview-py/tests/` directory (auto-indexed) |

## Usage

### Quick start (recommended)

Clone, build, and run as a long-running local HTTP service. The default image is lean — `search_test_examples` reads the upstream `openreview-py/tests/` directory from a bind-mount, so point `-v` at your local checkout (every openreview-py developer has one):

```bash
git clone https://github.com/openreview/openreview-mcp.git
cd openreview-mcp
docker build -t openreview-mcp .

# Adjust the path to your local openreview-py checkout
docker run -d --name openreview-mcp -p 8080:8080 \
  -v /path/to/your/openreview-py:/openreview-py \
  openreview-mcp --transport streamable-http
```

No env var needed — the image already sets `OPENREVIEW_KNOWLEDGE_PATH=/openreview-py`. Drop the `-v` flag if you don't need `search_test_examples`; the other two tools (`search_api`, `get_method_signature`) work without any mount, and the tests-index tool returns a clear "disabled" message.

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

Restart Claude Code (`/exit` and relaunch). All 3 tools become available; `search_test_examples` indexes the bind-mounted `openreview-py/tests/` directory at container start.

**To stop the server:**

```bash
docker stop openreview-mcp && docker rm openreview-mcp
```

**To upgrade later** (picks up new `openreview-mcp` code and new upstream `openreview-py` for the introspection layer):

```bash
git pull && docker build --no-cache -t openreview-mcp .
docker stop openreview-mcp && docker rm openreview-mcp
docker run -d --name openreview-mcp -p 8080:8080 \
  -v /path/to/your/openreview-py:/openreview-py \
  openreview-mcp --transport streamable-http
```

`--no-cache` forces pip to refetch the latest `openreview-py` for introspection. The tests-index comes from your bind-mount, so `git pull` in `/path/to/your/openreview-py` is what refreshes that layer — no image rebuild needed for upstream-test changes.

### Build a self-contained image (Cloud Run / VM deployments)

When the host filesystem won't be available — e.g., shipping to Cloud Run, a managed VM, or a teammate without an `openreview-py` clone — opt in to baking a shallow upstream clone into the image:

```bash
docker build --build-arg CLONE_OPENREVIEW_PY=true -t openreview-mcp:full .

docker run -d --name openreview-mcp -p 8080:8080 \
  openreview-mcp:full --transport streamable-http
```

Adds ~60 MB and an implicit dependency on GitHub at build time, but no `-v` needed at runtime. A runtime bind-mount at `/openreview-py` still works and transparently replaces the baked-in clone for live-edit workflows.

### Alternative: stdio per-call (no long-running service)

If you'd rather Claude Code spawn a fresh container on every tool call (lower idle footprint, but introspection + index rebuild on each invocation):

```json
{
  "mcpServers": {
    "openreview": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/path/to/your/openreview-py:/openreview-py",
        "openreview-mcp"
      ]
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
| `OPENREVIEW_KNOWLEDGE_PATH` | Directory hint for `search_test_examples`. The Dockerfile sets this to `/openreview-py` by default — bind-mount your local checkout there, or use `--build-arg CLONE_OPENREVIEW_PY=true` to bake an upstream clone into the image. The `tests/` subdir under this path is what `search_test_examples` indexes; if it doesn't exist, the tool returns a clear disabled message and the other two tools work unaffected. |
| `OPENREVIEW_TESTS_PATH` | Explicit override for the `tests/` directory used by `search_test_examples`. Falls back to `{OPENREVIEW_KNOWLEDGE_PATH}/tests/`. |

## Reusable Registration

Other FastMCP servers can mount the knowledge tools without running the full server:

```python
from openreview_mcp.registration import register_knowledge_tools

register_knowledge_tools(mcp)  # mounts 3 knowledge tools onto your FastMCP instance
```

## Keeping Up with openreview-py

The server has two layers, each with a different freshness story:

- **Introspection** (`search_api`, `get_method_signature`) — reads the installed `openreview-py` at startup. Refreshes when you rebuild the image; `--no-cache` forces pip to refetch upstream `main`.
- **Test-suite index** (`search_test_examples`) — AST-indexed at startup from the `tests/` subdir of `/openreview-py` inside the container. Default workflow: bind-mount your local `openreview-py` checkout at `/openreview-py`; `git pull` in that checkout + restart the container refreshes the index. For self-contained builds (Cloud Run / VM), opt in with `--build-arg CLONE_OPENREVIEW_PY=true` and `docker build --no-cache` re-fetches upstream.

## Development

```bash
git clone https://github.com/openreview/openreview-mcp.git
cd openreview-mcp
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/ -v
```
