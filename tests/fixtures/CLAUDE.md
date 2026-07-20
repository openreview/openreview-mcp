# tests/fixtures/

Hermetic fixtures backing the tests-index unit tests.

## Files

- `fake_tests/` — Synthetic openreview-py-style test corpus used by `test_tests_index.py` and the `search_test_examples` registration tests. Contains a stub `conftest.py` with a `Helpers` class plus clean class-based + top-level test files, a long-body method (for truncation testing), and a selenium-tainted file (for exclusion testing). See `test_tests_index.py` for the exact asserted shape.

## Editing rules

These are **test fixtures, not live knowledge**.

Before editing the fixture, grep `tests/test_tests_index.py` and `tests/test_tools.py` for the asserted strings — tests will silently drift if you add or remove content. In particular:

- `test_tests_index.py::TestBuildTestIndex` asserts specific `(class_name, func_name)` tuples and token presence for the `fake_tests/` corpus.

The `pyproject.toml` `norecursedirs = ["tests/fixtures"]` setting prevents pytest from collecting the fake test files as real tests.
