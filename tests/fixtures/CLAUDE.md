# tests/fixtures/

Minimal fixture versions of the static knowledge files, used exclusively by `test_knowledge.py`.

## Files

- `llm.txt` — Must contain exactly these four `## ` sections (hardcoded in `test_knowledge.py::TestLoadKnowledge::test_parses_llm_txt_sections`):
  - `Authentication` (must mention "Token auth" and "username")
  - `Content Structure`
  - `Conference Workflow` (must contain "Venue Request" and "Deploy")
  - `Anti-Patterns to Avoid`
- `examples.md` — Must contain `## ` sections `Authentication`, `Notes`, `Conference Workflow`, with code blocks that include `post_note_edit` under "Submit a paper".

## Editing rules

These are **test fixtures, not live knowledge**. The real `llm.txt` and `examples.md` live in the `openreview-py` repo (referenced via `OPENREVIEW_KNOWLEDGE_PATH`).

Before editing either file, grep `tests/test_knowledge.py` and `tests/test_tools.py` for the asserted strings — tests will silently drift if you add or remove sections. In particular:

- `test_knowledge.py::test_parses_llm_txt_sections` asserts exactly 4 practice sections.
- `test_knowledge.py::test_finds_code_blocks` asserts `"submit paper"` search returns content containing `"post_note_edit"` and a Python code fence.
- `test_knowledge.py::test_conference` asserts workflow("conference") returns content with `"Venue Request"`, `"Deploy"`, and a `python` code fence.
- `test_knowledge.py::test_journal` asserts workflow("journal") returns empty (**do not add a journal section**).
