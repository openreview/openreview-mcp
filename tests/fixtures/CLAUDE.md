# tests/fixtures/

Hermetic fixtures backing the parser and tests-index unit tests.

## Files

- `llm.txt` — Minimal fixture version of the static knowledge file used by `test_knowledge.py`. Must contain exactly these four `## ` sections (hardcoded in `test_knowledge.py::TestLoadKnowledge::test_parses_llm_txt_sections`):
  - `Authentication` (must mention "Token auth" and "username")
  - `Content Structure`
  - `Conference Workflow`
  - `Anti-Patterns to Avoid`
- `fake_tests/` — Synthetic openreview-py-style test corpus used by `test_tests_index.py` and the `search_test_examples` registration tests. Contains a stub `conftest.py` with a `Helpers` class plus clean class-based + top-level test files, a long-body method (for truncation testing), and a selenium-tainted file (for exclusion testing). See `test_tests_index.py` for the exact asserted shape.

## Editing rules

These are **test fixtures, not live knowledge**. The real `llm.txt` is bundled inside the package at `openreview_mcp/knowledge_files/` (copied verbatim from the upstream `openreview-py` repo at release time). The `OPENREVIEW_KNOWLEDGE_PATH` env var overrides the bundled default at runtime for development against a live checkout.

Before editing either fixture, grep `tests/test_knowledge.py`, `tests/test_tests_index.py`, and `tests/test_tools.py` for the asserted strings — tests will silently drift if you add or remove sections. In particular:

- `test_knowledge.py::test_parses_llm_txt_sections` asserts exactly 4 practice sections.
- `test_tools.py::test_get_best_practices_returns_section` asserts `topic="authentication"` returns content containing `"token"`.
- `test_tests_index.py::TestBuildTestIndex` asserts specific `(class_name, func_name)` tuples and token presence for the `fake_tests/` corpus.

The `pyproject.toml` `norecursedirs = ["tests/fixtures"]` setting prevents pytest from collecting the fake test files as real tests.
