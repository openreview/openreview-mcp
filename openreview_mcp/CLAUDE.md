# src/

FastMCP server implementation. Three modules correspond to the project's two knowledge layers plus the server entry point.

## Files

- `server.py` — FastMCP server entry point. Defines the 5 `@mcp.tool()` decorated functions (`search_api`, `get_method_signature`, `get_best_practices`, `get_code_example`, `get_workflow_guide`) and the `main()` entry point (`mcp.run(transport="stdio")`). Startup builds the introspection cache and loads the knowledge base once at module import — tools then read from these in-memory structures. Formatting helpers `_format_search_results` and `_format_method_details` render introspection dicts into concise Markdown strings for LLM consumption.
- `introspection.py` — Live introspection of the installed `openreview-py` package using Python's `inspect` module. `TARGET_CLASSES` lists the (module, class) pairs to introspect; `TARGET_MODULES` lists modules whose top-level functions are introspected as pseudo-classes. `search_methods()` ranks by exact name > name contains > docstring contains > param contains and caps results at 15. `get_method_details()` returns exact + partial name matches.
- `knowledge.py` — Parser for the static knowledge files. `KnowledgeBase` is a dataclass holding `practices` (from `llm.txt`) and `examples` (from `examples.md`) as dicts keyed by `## ` section header. `search_best_practices()` ranks header matches above content matches. `get_workflow()` combines practices + examples sections for conference/journal/stage queries.
- `__init__.py` — Empty package marker.

## Important patterns

- Tool functions return plain strings. LLMs consume the output directly, so keep formatting concise and avoid repetition.
- All heavy work (introspection, knowledge parsing) happens once at module import time. Tools are cheap reads against module-level caches (`_introspection_cache`, `_knowledge_base`).
- `server.py` optionally imports `openreview_tools` and calls `register_tools(mcp)` if the package is installed AND `OPENREVIEW_API_TOKEN` is set — this is the plugin hook for `openreview-tools-mcp` live API tools. Failure to import is silent by design.
- Environment variables: `OPENREVIEW_KNOWLEDGE_PATH` (directory containing `llm.txt` + `examples.md`), `MCP_HOST`, `MCP_PORT`, `OPENREVIEW_API_TOKEN`.
- Imports use `from src.xxx import ...` — the package is run as `python -m src.server`, not as a standalone module.

## When editing

- Adding a tool: decorate with `@mcp.tool()`, give it a clear Args docstring (visible to the LLM), return a string.
- Adding an introspection target: append to `TARGET_CLASSES` (for classes) or `TARGET_MODULES` (for standalone functions). Private methods are skipped except `__init__`.
- Changing result formatting: update the `_format_*` helpers in `server.py`, not the introspection layer — introspection returns raw dicts.
