"""FastMCP server for exposing openreview-py library structure."""

import json
from typing import Any, Dict, List

from fastmcp import FastMCP

from src.introspect import (
    get_openreview_functions,
    get_openreview_classes, 
    search_openreview_functions,
    get_library_overview
)

# Initialize FastMCP server
mcp = FastMCP("OpenReview Python Library MCP Server")


@mcp.tool()
def list_openreview_functions(filter_by_module: str = None) -> List[Dict[str, Any]]:
    """
    Get a list of all available functions from the openreview-py library.
    
    Args:
        filter_by_module: Optional module name to filter functions (e.g., 'openreview.api')
        
    Returns:
        JSON array of functions with name, docstring, module, signature, and type
    """
    functions = get_openreview_functions()
    
    # TODO: Implement more sophisticated filtering
    # - Filter by function type (constructor, method, function)
    # - Filter by parameter count or complexity
    # - Sort by relevance or alphabetical order
    if filter_by_module:
        functions = [f for f in functions if f.get("module") == filter_by_module]
    
    return functions


@mcp.tool()
def list_openreview_classes(include_methods: bool = True) -> List[Dict[str, Any]]:
    """
    Get a list of all available classes from the openreview-py library.
    
    Args:
        include_methods: Whether to include class methods in the response
        
    Returns:
        JSON array of classes with name, docstring, module, and optionally methods
    """
    classes = get_openreview_classes()
    
    # TODO: Add more filtering options:
    # - Filter by inheritance hierarchy  
    # - Filter by class type (abstract, concrete, mixin)
    # - Include/exclude private methods
    # - Add property information
    if not include_methods:
        for cls in classes:
            cls.pop("methods", None)
    
    return classes


@mcp.tool()
def search_openreview_api(query: str) -> List[Dict[str, Any]]:
    """
    Search for functions and classes by name or keyword in docstrings.
    
    Args:
        query: Search term to find in function/class names or documentation
        
    Returns:
        JSON array of matching functions and classes
    """
    if not query or not query.strip():
        return []
    
    # TODO: Enhance search capabilities:
    # - Search across both functions and classes
    # - Implement fuzzy matching
    # - Add search result ranking
    # - Support advanced query syntax (AND, OR, NOT)
    # - Search in parameter names and types
    matching_functions = search_openreview_functions(query.strip())
    
    # TODO: Also search classes and their methods
    # matching_classes = search_openreview_classes(query.strip())
    # return matching_functions + matching_classes
    
    return matching_functions


@mcp.tool()
def get_openreview_overview() -> Dict[str, Any]:
    """
    Get a comprehensive overview of the entire openreview-py library structure.
    
    Returns:
        Dictionary containing functions, classes, modules, and statistics
    """
    overview = get_library_overview()
    
    # TODO: Add more comprehensive information:
    # - Recent changes and version history
    # - Usage examples for common patterns
    # - API endpoint mappings
    # - Error handling patterns
    # - Configuration options
    
    return overview


@mcp.tool() 
def get_function_details(function_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific function.
    
    Args:
        function_name: Name of the function to get details for
        
    Returns:
        Detailed function information including parameters, return types, examples
    """
    functions = get_openreview_functions()
    
    # Find the function by name
    for func in functions:
        if func["name"] == function_name:
            # TODO: Add more detailed information:
            # - Parameter types and descriptions
            # - Return type information  
            # - Usage examples
            # - Related functions
            # - Error conditions
            return {
                **func,
                "parameters": [],  # TODO: Extract parameter info
                "return_type": "unknown",  # TODO: Extract return type
                "examples": [],  # TODO: Add usage examples
                "related_functions": []  # TODO: Find related functions
            }
    
    return {"error": f"Function '{function_name}' not found"}


def main():
    """Run the FastMCP server."""
    # TODO: Add configuration options:
    # - Custom port configuration
    # - Logging level settings
    # - Cache configuration for introspection results
    # - Module inclusion/exclusion filters
    # - Performance monitoring
    
    print("Starting OpenReview Python Library MCP Server (HTTP mode)...")
    print("Available tools:")
    print("- list_openreview_functions: List all available functions")
    print("- list_openreview_classes: List all available classes") 
    print("- search_openreview_api: Search functions by keyword")
    print("- get_openreview_overview: Get library overview")
    print("- get_function_details: Get detailed function information")
    print()
    
    # Start the FastMCP server with HTTP transport
    # You can configure host/port via environment variables or here
    import os
    host = os.environ.get("MCP_HOST", "localhost")
    port = int(os.environ.get("MCP_PORT", "4000"))
    
    # Set base path to root instead of /mcp
    mcp.run(transport="http", host=host, port=port, path="/")


if __name__ == "__main__":
    main()
