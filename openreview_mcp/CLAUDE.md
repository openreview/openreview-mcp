# openreview_mcp/

The installable Python package. Houses the `register_knowledge_tools` public API, the data/logic layers it uses, the standalone FastMCP entry point, and the bundled static knowledge files.

## Files

- `__init__.py` — Re-exports `register_knowledge_tools` as the package's public API. Zero import side effects.
- `registration.py` — Reusable `register_knowledge_tools(mcp, knowledge_path=None) -> dict[str, Callable[..., str]]`. Builds the introspection cache and knowledge base at CALL time (not import time), then defines the 5 tools as closures via `@mcp.tool()` and registers them on the passed-in FastMCP instance. Returns a dict of tool handles keyed by name. Downstream consumers import this function and mount the knowledge tools onto their own FastMCP instance.
- `server.py` — Thin standalone entry point (~27 lines). Creates its own `FastMCP`, calls `register_knowledge_tools(mcp)`, provides `main()` for the `openreview-mcp` CLI script. This is the only module that does work at import time, and only because it IS the standalone CLI entry point.
- `introspection.py` — Live introspection of the installed `openreview-py` package using Python's `inspect` module. `TARGET_CLASSES` lists the (module, class) pairs to introspect; `TARGET_MODULES` lists modules whose top-level functions are introspected as pseudo-classes. `search_methods()` ranks by exact name > name contains > docstring contains > param contains and caps results at 15. `get_method_details()` returns exact + partial name matches.
- `knowledge.py` — Parser for the static knowledge files. `KnowledgeBase` is a dataclass holding `practices` (from `llm.txt`) and `examples` (from `examples.md`) as dicts keyed by `## ` section header. `search_best_practices()` ranks header matches above content matches. `get_workflow()` combines practices + examples for conference/journal/stage queries.
- `knowledge_files/` — Bundled `llm.txt` and `examples.md`, synced verbatim from the upstream `openreview-py` repo. These are the default knowledge source when `OPENREVIEW_KNOWLEDGE_PATH` is unset.

## Important patterns

- **Zero import side effects in `registration.py`.** No module-level FastMCP creation, no introspection at import, no knowledge loading at import. This is load-bearing: it lets downstream packages import `register_knowledge_tools` without accidentally spinning up a server or eating the introspection cost.
- **`server.py` is the only module that does work at import time,** and only because it IS the standalone CLI entry point. Running `openreview-mcp` on the CLI is the only code path that creates a module-level FastMCP here.
- **Tool functions return plain strings.** LLMs consume the output directly, so keep formatting concise and avoid repetition.
- **`register_knowledge_tools` returns `dict[str, Callable[..., str]]`** keyed by tool name. Production code typically ignores the return value; tests use it to invoke tools directly as plain callables: `handles["search_api"](query="...")`. Note: fastmcp 3.2.2's `@mcp.tool()` decorator registers the tool internally on the `FastMCP` instance but leaves the calling-scope name as the plain function — there is no `.fn` attribute on decorated functions.
- **Knowledge path resolution priority**: explicit `knowledge_path` arg > `OPENREVIEW_KNOWLEDGE_PATH` env var > bundled `knowledge_files/` directory. All resolution happens inside `register_knowledge_tools` via `_resolve_knowledge_path`, not at module level.
- **No environment variable reads at module level.** Downstream consumers can set env vars after import, or override with the explicit `knowledge_path` argument.

## When editing

- **Adding a tool**: add a new `@mcp.tool()`-decorated closure inside `register_knowledge_tools`, give it a clear `Args:` docstring (visible to the LLM), make sure it returns a string, and add it to the returned dict.
- **Adding an introspection target**: append to `TARGET_CLASSES` (for classes) or `TARGET_MODULES` (for top-level functions) in `introspection.py`. Private methods are skipped except `__init__`.
- **Changing result formatting**: update `_format_search_results` or `_format_method_details` in `registration.py`.
- **Updating bundled knowledge**: `cp /path/to/openreview-py/llm.txt openreview_mcp/knowledge_files/` then same for `examples.md`. There is no auto-sync — this is a manual step at release time. `tests/test_bundled_knowledge.py` catches a missed sync by asserting the bundled files exist and parse to non-empty sections.
