# OpenReview MCP Server Redesign

## Context

The openreview-py library needs an MCP server that helps LLMs write correct openreview-py code. The existing server has 11 tools backed by static metadata (hand-maintained dicts in `introspect.py`). This redesign replaces all existing tools with 5 new tools powered by live Python introspection of the installed openreview-py package and static knowledge files (llm.txt, examples.md) for best practices and workflows.

**Primary use case:** Users connect this MCP server to Claude Code, Cursor, or similar tools and ask them to write openreview-py code (e.g., "set up a venue with double-blind review").

**Secondary use case:** Users ask documentation-style questions about the OpenReview platform.

## Architecture

Two knowledge layers, no external network dependencies:

### Live Introspection Layer
- Imports `openreview` and `openreview.api` at server startup
- Uses Python's `inspect` module to extract method signatures, docstrings, parameter types, default values, and module paths from all classes
- Target classes: `openreview.api.OpenReviewClient`, `openreview.Client`, `openreview.api.Note`, `openreview.api.Invitation`, `openreview.api.Edge`, `openreview.api.Group`, `openreview.api.Tag`, `openreview.api.Edit`, `openreview.openreview.Profile`, `openreview.venue.Venue`
- Results cached in memory at startup (dict keyed by class name -> method name)
- Adding docstrings or methods to openreview-py is automatically picked up on server restart

### Static Knowledge Layer
- Reads `llm.txt` and `examples.md` from a configurable file path (defaults to the local openreview-py repo root)
- Parses into indexed sections at startup:
  - `llm.txt` is split by `## ` headers into a dict of `{section_name: section_content}`
  - `examples.md` is split by `## ` and `### ` headers into a dict of `{section_name: section_content}`
- Matching is case-insensitive keyword search against section headers and content

## Tool Definitions

### Tool 1: `search_api`

**Purpose:** Search all introspected methods and classes by keyword.

**Parameters:**
- `query` (str, required): search term (e.g., "edge", "post note", "profile merge")
- `class_name` (str, optional): filter to a specific class (e.g., "OpenReviewClient", "Note", "Venue")

**Behavior:**
- Matches `query` against method names, docstrings, and parameter names (case-insensitive)
- If `class_name` is provided, only search within that class
- Returns max 15 results, sorted by relevance (exact name match > name contains > docstring contains > param contains)

**Returns:** List of matching methods with: class name, method name, signature (params with types/defaults), and first line of docstring.

### Tool 2: `get_method_signature`

**Purpose:** Return full details for a specific method.

**Parameters:**
- `method_name` (str, required): exact or partial method name (e.g., "post_note_edit", "get_all_notes")

**Behavior:**
- Searches all classes for methods matching the name (exact match first, then partial)
- If multiple matches, returns all of them
- Extracts full docstring, all parameters with types and defaults, return type annotation

**Returns:** For each match: class path, full signature, complete docstring, parameter details, return type.

### Tool 3: `get_best_practices`

**Purpose:** Return relevant section(s) from `llm.txt` for a topic.

**Parameters:**
- `topic` (str, required): keyword or phrase (e.g., "authentication", "permissions", "anti-patterns", "date handling")

**Behavior:**
- Matches `topic` (case-insensitive) against section headers first, then section content
- Returns all matching sections, header matches ranked above content matches

**Returns:** The matching section(s) as-is from llm.txt, with their headers.

### Tool 4: `get_code_example`

**Purpose:** Return matching code snippet(s) from `examples.md`.

**Parameters:**
- `operation` (str, required): what the user wants to do (e.g., "submit paper", "post edge", "recruit reviewers")

**Behavior:**
- Matches `operation` (case-insensitive) against section headers and code block comments
- Returns all matching sections with their code blocks

**Returns:** Matching section header + description + code block(s).

### Tool 5: `get_workflow_guide`

**Purpose:** Return the full workflow for a venue type with inline code examples.

**Parameters:**
- `workflow_type` (str, required): "conference", "journal", or a specific stage like "matching", "review", "decision", "submission", "recruitment"

**Behavior:**
- For "conference" or "journal": returns the full workflow section from llm.txt, then appends all matching code examples from examples.md for each stage
- For a specific stage: returns just that stage's description from llm.txt + matching examples from examples.md

**Returns:** Ordered workflow steps with descriptions and code examples inlined.

## File Structure

```
openreview-mcp/
├── src/
│   ├── server.py           # FastMCP server + 5 tool definitions
│   ├── introspection.py    # Live introspection of openreview-py (replaces introspect.py)
│   ├── knowledge.py        # Static knowledge parser (llm.txt + examples.md)
│   └── __init__.py
├── docs/
│   ├── DEPLOYMENT.md
│   └── superpowers/specs/
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

### Module Responsibilities

**`introspection.py`** (~150-200 lines):
- `introspect_library() -> dict` — imports openreview, inspects all target classes, returns structured metadata
- `search_methods(query, class_name, cache) -> list` — search with relevance ranking
- `get_method_details(method_name, cache) -> list` — full method details

**`knowledge.py`** (~100-150 lines):
- `KnowledgeBase` dataclass: `practices: dict[str, str]` (llm.txt sections keyed by header), `examples: dict[str, str]` (examples.md sections keyed by header)
- `load_knowledge(llm_txt_path, examples_md_path) -> KnowledgeBase` — parse and index both files
- `search_best_practices(topic, kb) -> str` — match against llm.txt sections
- `search_examples(operation, kb) -> str` — match against examples.md sections
- `get_workflow(workflow_type, kb) -> str` — combine workflow + examples

**`server.py`** (~150-200 lines):
- FastMCP server setup with 5 tool registrations
- Startup: call `introspect_library()` and `load_knowledge()`, store in module-level state
- Each tool function is thin — delegates to introspection.py or knowledge.py
- Configurable via environment variables: `OPENREVIEW_PY_PATH` (path to llm.txt/examples.md), `MCP_HOST`, `MCP_PORT`

## Configuration

Environment variables:
- `OPENREVIEW_KNOWLEDGE_PATH`: path to directory containing `llm.txt` and `examples.md` (defaults to `../openreview-py/` relative to server)
- `MCP_HOST`: server host (default: `localhost`)
- `MCP_PORT`: server port (default: `4000`)

## Dependencies

- `fastmcp>=0.1.0` (existing)
- `openreview-py` (existing, installed from GitHub)
- No new dependencies needed — `inspect` is stdlib

## What Gets Removed

- `src/introspect.py` (2,251 lines of static metadata) — replaced by live introspection
- All 11 existing tool definitions in `server.py` — replaced by 5 new tools

## Test Plan

Tests are written **before** implementation (TDD). Three layers:

### Layer 1: Unit Tests — Introspection (`tests/test_introspection.py`)

Tests for `introspection.py` functions using the real installed `openreview-py` package:

1. `test_introspect_library_returns_all_target_classes` — cache contains keys for OpenReviewClient, Client, Note, Invitation, Edge, Group, Tag, Edit, Profile, Venue
2. `test_introspect_library_captures_method_signatures` — OpenReviewClient has `post_note_edit` with params `invitation`, `signatures`, `note`, `await_process`
3. `test_introspect_library_captures_docstrings` — methods with docstrings have non-empty docstring field
4. `test_search_methods_exact_name_match` — searching "post_note_edit" returns it as first result
5. `test_search_methods_partial_name_match` — searching "post_note" returns both `post_note_edit` and `post_note_edit_as_guest`
6. `test_search_methods_docstring_match` — searching for a keyword that only appears in docstrings returns results
7. `test_search_methods_class_filter` — searching with `class_name="Venue"` only returns Venue methods
8. `test_search_methods_max_results` — returns at most 15 results
9. `test_search_methods_relevance_ordering` — exact name match ranks above partial match ranks above docstring match
10. `test_get_method_details_returns_full_info` — `get_method_details("post_note_edit")` returns class path, signature, docstring, params, return type
11. `test_get_method_details_partial_match` — "get_all" returns `get_all_notes`, `get_all_edges`, etc.
12. `test_get_method_details_no_match` — returns empty list for nonsense input
13. `test_introspect_skips_private_methods` — methods starting with `_` are excluded

### Layer 2: Unit Tests — Knowledge (`tests/test_knowledge.py`)

Tests for `knowledge.py` functions using fixture markdown files:

1. `test_load_knowledge_parses_llm_txt_sections` — fixture llm.txt with 3 sections produces dict with 3 keys
2. `test_load_knowledge_parses_examples_md_sections` — fixture examples.md with nested `##`/`###` headers produces correct keys
3. `test_load_knowledge_missing_file_raises` — raises FileNotFoundError with clear message
4. `test_search_best_practices_header_match` — searching "Authentication" returns the auth section
5. `test_search_best_practices_content_match` — searching "token" matches sections containing that word
6. `test_search_best_practices_case_insensitive` — "AUTHENTICATION" matches "Authentication"
7. `test_search_best_practices_no_match` — returns empty string for nonsense input
8. `test_search_best_practices_header_ranked_above_content` — header match appears before content-only match
9. `test_search_examples_finds_code_blocks` — searching "submit paper" returns section with ```python block
10. `test_search_examples_no_match` — returns empty string for nonsense input
11. `test_get_workflow_conference` — returns conference workflow section + matching examples
12. `test_get_workflow_journal` — returns journal workflow section + matching examples
13. `test_get_workflow_specific_stage` — "matching" returns just the matching stage description + examples

### Layer 3: Tool Tests (`tests/test_tools.py`)

Tests that call MCP tools via FastMCP without starting a server:

1. `test_search_api_returns_results` — calling `search_api(query="post_note")` returns formatted string containing `post_note_edit`
2. `test_search_api_with_class_filter` — calling `search_api(query="setup", class_name="Venue")` returns only Venue methods
3. `test_get_method_signature_returns_details` — calling `get_method_signature(method_name="post_note_edit")` returns full signature with all params
4. `test_get_best_practices_returns_section` — calling `get_best_practices(topic="authentication")` returns content about token auth, env vars
5. `test_get_code_example_returns_snippet` — calling `get_code_example(operation="submit paper")` returns Python code block
6. `test_get_workflow_guide_conference` — calling `get_workflow_guide(workflow_type="conference")` returns ordered steps with code
7. `test_get_workflow_guide_journal` — calling `get_workflow_guide(workflow_type="journal")` returns ordered steps with code

### Test Fixtures

- `tests/fixtures/llm.txt` — minimal version of llm.txt with 3-4 sections (Authentication, Content Structure, Conference Workflow, Anti-Patterns)
- `tests/fixtures/examples.md` — minimal version of examples.md with 3-4 sections (Authentication, Notes, Conference Workflow)
- Layer 3 tests use the real `llm.txt` and `examples.md` from the openreview-py repo

### Implementation Order

1. Write all test files with tests that initially fail
2. Implement `introspection.py` — Layer 1 tests pass
3. Implement `knowledge.py` — Layer 2 tests pass
4. Implement `server.py` — Layer 3 tests pass

## Verification

1. `pytest tests/` — all tests pass
2. Start the server: `uv run src/server.py`
3. Verify all 5 tools appear in tool list
4. Connect to Claude Code via MCP config and ask it to "write code to submit a paper to a venue" — verify it uses the tools and produces correct code
