# tests/

Pytest suite mirroring the three-layer architecture in `src/`.

## Files

- `conftest.py` — Shared fixtures: `fixtures_dir`, `llm_txt_path`, `examples_md_path`. All resolve paths under `tests/fixtures/`.
- `test_introspection.py` — Unit tests for `src/introspection.py`. **Requires `openreview-py` installed** (editable or otherwise) because it calls `introspect_library()` against the real package. Covers class discovery, method signature capture, docstring capture, private method skipping, search ranking (exact > partial > docstring > param), class filtering, and the 15-result cap.
- `test_knowledge.py` — Unit tests for `src/knowledge.py`. Uses the fixture files in `tests/fixtures/` — **does not require** `openreview-py` installed. Covers section parsing, header-ranked-above-content ordering, case insensitivity, and missing-file error handling.
- `test_tools.py` — Integration tests for the 5 MCP tools. Imports the tool objects from `src.server` and calls them via `.fn()` (FastMCP's `@mcp.tool()` decorator wraps the underlying function and exposes it on the `.fn` attribute). Importing `src.server` triggers the module-level introspection + knowledge load, so these tests also require `openreview-py` installed and `OPENREVIEW_KNOWLEDGE_PATH` pointing at a directory with real `llm.txt` / `examples.md`.
- `fixtures/` — Fixture `llm.txt` and `examples.md`. See `tests/fixtures/CLAUDE.md`.

## Running

```bash
OPENREVIEW_KNOWLEDGE_PATH=/path/to/openreview-py .venv/bin/python -m pytest tests/ -v
```

Run a single layer to skip the `openreview-py` dependency when iterating on the knowledge parser:

```bash
.venv/bin/python -m pytest tests/test_knowledge.py -v
```

## Gotchas

- `test_tools.py` imports `src.server`, which loads knowledge at import time. If `OPENREVIEW_KNOWLEDGE_PATH` is wrong, collection fails before any test runs.
- Tests assert against specific fixture content (e.g. `"Token auth"`, `"Venue Request"`, `"post_note_edit"`). Do not edit `tests/fixtures/*` casually — see that directory's CLAUDE.md.
- `test_introspection.py` asserts that `post_note_edit` exists on `OpenReviewClient` with parameters `invitation`, `signatures`, `note`, `await_process`. If the installed `openreview-py` changes these, tests will fail — the fix is usually to update the installed package, not the test.
