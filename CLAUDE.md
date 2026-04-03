Project Overview & Context:
This project is an MCP server built with FastMCP that helps LLMs write correct openreview-py code. It provides two knowledge layers: live introspection of the installed openreview-py library (method signatures, docstrings, class structures) and static knowledge files (best practices, code examples, workflow guides). The server exposes 5 tools that LLM clients use to find API methods, understand best practices, get code examples, and follow workflow patterns. Built with Python 3.11+ and uv package manager.

Project Structure:
```
openreview-mcp/
├── src/
│   ├── server.py           # FastMCP server + 5 tool definitions
│   ├── introspection.py    # Live introspection of openreview-py via inspect module
│   ├── knowledge.py        # Static knowledge parser (llm.txt + examples.md)
│   └── __init__.py
├── tests/
│   ├── test_introspection.py  # Layer 1: introspection unit tests
│   ├── test_knowledge.py      # Layer 2: knowledge parsing unit tests
│   ├── test_tools.py          # Layer 3: MCP tool integration tests
│   ├── conftest.py            # Shared fixtures
│   └── fixtures/              # Test fixture files
├── docs/
│   ├── DEPLOYMENT.md
│   └── superpowers/specs/     # Design specs
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

Key files: `src/server.py` (tool definitions), `src/introspection.py` (live introspection), `src/knowledge.py` (static knowledge).

Environment Variables:
- `OPENREVIEW_KNOWLEDGE_PATH`: path to directory containing `llm.txt` and `examples.md` (defaults to `../../openreview-py` relative to src/)

Tools (5 total):
1. `search_api(query, class_name?)` — Search methods/classes by keyword with relevance ranking
2. `get_method_signature(method_name)` — Full details for a specific method
3. `get_best_practices(topic)` — Best practices from llm.txt by topic
4. `get_code_example(operation)` — Code examples from examples.md
5. `get_workflow_guide(workflow_type)` — Step-by-step workflow guides with code

Code Style & Conventions:
- snake_case for files and functions, PascalCase for classes
- Docstrings on all public functions
- Avoid redundant information in tool output — LLMs need concise, non-repetitive context
- Use decorators (`@mcp.tool()`) to register tools

Running Tests:
```bash
OPENREVIEW_KNOWLEDGE_PATH=/path/to/openreview-py .venv/bin/python -m pytest tests/ -v
```
