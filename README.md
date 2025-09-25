# OpenReview Python MCP Server

A Model Context Protocol (MCP) server built with FastMCP that exposes the structure and documentation of the `openreview-py` library. This allows LLM clients to discover available classes, functions, and their documentation to generate accurate Python code examples using the OpenReview library.

## 🎯 Purpose

This MCP server provides **read-only access** to the `openreview-py` library's structure - no code execution or API calls are performed. It's designed to help LLMs understand and generate code using the OpenReview Python library by providing:

- Function signatures and documentation
- Class structures and methods
- Search capabilities across the library
- Comprehensive library overview

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- `uv` package manager

### Installation

1. **Clone and navigate to the project:**
```bash
cd openreview-mcp
```

2. **Install dependencies:**
```bash
uv sync
```

This will install:
- `fastmcp` - MCP server framework
- `openreview-py` - The library we're introspecting (from GitHub)
- Development tools (pytest, black, ruff, mypy)

### Running the Server

Start the MCP server:
```bash
uv run openreview-mcp
```

Or run directly:
```bash
uv run python src/server.py
```

The server will start and display available tools:
```
Starting OpenReview Python Library MCP Server...
Available tools:
- list_openreview_functions: List all available functions
- list_openreview_classes: List all available classes
- search_openreview_api: Search functions by keyword
- get_openreview_overview: Get library overview
- get_function_details: Get detailed function information
```

## 🛠️ Available MCP Tools

### 1. `list_openreview_functions`
Lists all available functions from the openreview-py library.

**Parameters:**
- `filter_by_module` (optional): Filter by specific module (e.g., "openreview.api")

**Returns:** Array of functions with name, docstring, module, signature, and type.

### 2. `list_openreview_classes` 
Lists all available classes from the openreview-py library.

**Parameters:**
- `include_methods` (default: true): Whether to include class methods

**Returns:** Array of classes with name, docstring, module, and methods.

### 3. `search_openreview_api`
Search for functions by name or keywords in docstrings.

**Parameters:**
- `query` (required): Search term

**Returns:** Array of matching functions.

### 4. `get_openreview_overview`
Get a comprehensive overview of the entire library.

**Returns:** Dictionary with functions, classes, modules, and statistics.

### 5. `get_function_details`
Get detailed information about a specific function.

**Parameters:**
- `function_name` (required): Name of the function

**Returns:** Detailed function information.

## 📁 Project Structure

```
openreview-mcp/
├── src/
│   ├── server.py          # FastMCP server implementation
│   ├── introspect.py      # Library introspection utilities
│   └── __init__.py        # (optional) package init
├── pyproject.toml         # Project configuration and dependencies
└── README.md              # This file
```

## 🔧 Development

### Current Implementation Status

**✅ Implemented:**
- Complete FastMCP server setup with 5 tools
- Project structure and configuration
- Stub implementations with realistic example data

**🚧 TODO - Future Enhancements:**

The current implementation uses stub data. Here's how to expand it:

#### 1. Real Library Introspection (`introspect.py`)
```python
# TODO: Replace stub implementations with real introspection
import openreview
import inspect

def get_openreview_functions():
    # Use inspect module to dynamically discover functions
    # Walk through openreview module and submodules
    # Extract real docstrings, signatures, parameters
    pass
```

#### 2. Enhanced Search (`server.py`)
```python
# TODO: Implement advanced search features
- Fuzzy string matching
- Search in parameter names and types  
- Regex pattern support
- Result ranking by relevance
```

#### 3. Caching and Performance
```python
# TODO: Add caching for introspection results
- Cache function/class discoveries
- Lazy loading of module information
- Performance monitoring and optimization
```

#### 4. Advanced Filtering
```python
# TODO: Add sophisticated filtering options
- Filter by function complexity
- Filter by parameter count
- Include/exclude private methods
- Filter by inheritance hierarchy
```

### Development Commands

```bash
# Install development dependencies
uv sync --dev

# Run tests (when implemented)
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check .

# Type checking
uv run mypy .
```

### Adding New MCP Tools

To add a new tool to the server:

1. **Define the tool function in `server.py`:**
```python
@mcp.tool()
def your_new_tool(param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Description of what your tool does.
    
    Args:
        param1: Description of parameter
        param2: Optional parameter with default
        
    Returns:
        Description of return value
    """
    # Implementation here
    return {"result": "your data"}
```

2. **Add any supporting logic to `introspect.py` if needed:**
```python
def supporting_function():
    """Helper function for your new tool."""
    pass
```

3. **Update the main() function to advertise the new tool:**
```python
def main():
    print("Available tools:")
    print("- your_new_tool: Description")
```

## 🔍 Usage Examples


### With Claude Desktop
Configure the server in your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "openreview": {
      "command": "uv",
      "args": ["run", "python", "/path/to/openreview-mcp/src/server.py"],
      "host": "localhost",
      "port": 4000
    }
  }
}
```

### With VS Code
You can also configure the MCP server in VS Code using the Model Context Protocol extension (or compatible MCP client):

1. Open the command palette and search for "MCP: Add Server" or open the MCP extension settings.
2. Make sure the port matches your deployment (default is 4000, or set MCP_PORT env variable).
3. Save and connect to the server from the MCP extension sidebar.

### Example Tool Usage
Once connected (in Claude Desktop or VS Code), you can ask:

> "What functions are available for working with notes in OpenReview?"

The client would use the `search_openreview_api` tool with query "note" to find relevant functions.

> "Show me all the classes in the openreview library"

The client would use `list_openreview_classes` to get the class information.

## 🤝 Contributing

Key areas for contribution:

1. **Implement real introspection** in `introspect.py` using Python's `inspect` module
2. **Add comprehensive error handling** for import failures and edge cases  
3. **Implement caching** for better performance
4. **Add tests** for all functionality
5. **Enhance search capabilities** with fuzzy matching and ranking

## ⚠️ Important Notes

- **Read-only**: This server only provides metadata - no code execution
- **No API calls**: No actual OpenReview API interactions
- **No authentication**: No API keys or credentials required
- **Educational**: Designed for code generation assistance, not production API usage

## 📄 License

This project is provided as-is for educational and development purposes.