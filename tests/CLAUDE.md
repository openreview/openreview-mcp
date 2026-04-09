# tests/

Pytest suite. Mirrors the package layers: introspection, knowledge parsing, registration function, tool behavior, and a bundling regression guard.

## Files

- `conftest.py` — Shared fixtures: `fixtures_dir`, `llm_txt_path`, `examples_md_path`. All resolve paths under `tests/fixtures/`.
- `test_introspection.py` — Unit tests for `openreview_mcp/introspection.py`. **Requires `openreview-py` installed** because it calls `introspect_library()` against the real package. Covers class discovery, method signature capture, docstring capture, private method skipping, and search ranking (exact > partial > docstring > param).
- `test_knowledge.py` — Unit tests for `openreview_mcp/knowledge.py`. Uses the fixture files in `tests/fixtures/` — **does not require** `openreview-py` installed. Covers section parsing, header-ranked-above-content ordering, case insensitivity, and missing-file error handling.
- `test_bundled_knowledge.py` — Release-time regression guard. Asserts `llm.txt` and `examples.md` ship inside `openreview_mcp/knowledge_files/` and load into non-empty practice/example sections. Catches a missed manual sync from upstream openreview-py at release time.
- `test_registration.py` — Tests for `register_knowledge_tools` itself. Asserts all 5 tools register on a fresh `FastMCP`, the returned dict has exactly the 5 expected keys, invoking a handle calls into real introspection data, and the `knowledge_path` override parameter takes precedence over `OPENREVIEW_KNOWLEDGE_PATH`.
- `test_tools.py` — Behavior tests for the 5 tools. Uses a module-scoped `tools` fixture that creates a fresh `FastMCP` and calls `register_knowledge_tools(mcp)`, then invokes each tool via `tools["<name>"](kwarg=...)`.
- `fixtures/` — Minimal fixture `llm.txt` and `examples.md` for the parser tests. See `tests/fixtures/CLAUDE.md`.

## Running

```bash
.venv/bin/python -m pytest tests/ -v
```

No environment variables required — tests use the bundled knowledge files inside the package. Set `OPENREVIEW_KNOWLEDGE_PATH=/path/to/openreview-py` only if you want to verify against a live upstream checkout.

## Gotchas

- Tests call the 5 tools via the dict returned by `register_knowledge_tools`, not by importing names from `openreview_mcp.server` — tools are closures inside `register_knowledge_tools`, not module-level names. fastmcp 3.2.2's `@mcp.tool()` decorator leaves the scope binding as the plain function (no `.fn` attribute), so handles are invoked directly.
- Fixture files in `tests/fixtures/` are asserted against specific content (e.g., `"Token auth"`, `"Venue Request"`, `"post_note_edit"`). Do not edit them casually — see `tests/fixtures/CLAUDE.md` for the contract.
- `test_introspection.py` asserts that `post_note_edit` exists on `OpenReviewClient` with parameters `invitation`, `signatures`, `note`, `await_process`. If the installed `openreview-py` changes these, tests will fail — the fix is usually to update the installed package, not the test.
- `test_bundled_knowledge.py` will fail if the bundled files are missing or unparseable. The fix is to re-copy from upstream openreview-py.
