# tests/

Pytest suite. Mirrors the package layers: introspection, tests-index, registration function, and tool behavior.

## Files

- `conftest.py` — Shared fixtures: `fixtures_dir`, which resolves paths under `tests/fixtures/`.
- `test_introspection.py` — Unit tests for `openreview_mcp/introspection.py`. **Requires `openreview-py` installed** because it calls `introspect_library()` against the real package. Covers class discovery, method signature capture, docstring capture, private method skipping, API-version tagging, and search ranking (exact > partial > docstring > param).
- `test_tests_index.py` — Unit tests for `openreview_mcp/tests_index.py`. Uses the hermetic `tests/fixtures/fake_tests/` corpus — **does not require** the upstream `openreview-py/tests/` checkout. Covers AST indexing, selenium exclusion, token postings, scoring, body truncation, fixtures preamble, helpers footer, and malformed-AST graceful skip.
- `test_registration.py` — Tests for `register_knowledge_tools` itself. Asserts all 3 tools register on a fresh `FastMCP`, the returned dict has exactly the 3 expected keys, invoking a handle calls into real introspection data, and `search_test_examples` resolves a tests directory in the right priority order (explicit arg > env var > `{knowledge_path}/tests/` auto-detect).
- `test_tools.py` — Behavior tests for the 3 tools. Uses a module-scoped `tools` fixture that creates a fresh `FastMCP` and calls `register_knowledge_tools(mcp)`, then invokes each tool via `tools["<name>"](kwarg=...)`.
- `fixtures/` — `fake_tests/` for the tests-index tests. See `tests/fixtures/CLAUDE.md`.

## Running

```bash
.venv/bin/python -m pytest tests/ -v
```

No environment variables required — tests use the hermetic fixtures in `tests/fixtures/`.

## Gotchas

- Tests call the 3 tools via the dict returned by `register_knowledge_tools`, not by importing names from `openreview_mcp.server` — tools are closures inside `register_knowledge_tools`, not module-level names. fastmcp's `@mcp.tool()` decorator leaves the scope binding as the plain function (no `.fn` attribute), so handles are invoked directly.
- Fixture files in `tests/fixtures/fake_tests/` are asserted against specific content (e.g., `"post_note_edit"`). Do not edit them casually — see `tests/fixtures/CLAUDE.md` for the contract.
- `test_introspection.py` asserts that `post_note_edit` exists on `OpenReviewClient` with parameters `invitation`, `signatures`, `note`, `await_process`. If the installed `openreview-py` changes these, tests will fail — the fix is usually to update the installed package, not the test.
