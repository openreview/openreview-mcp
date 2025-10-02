"""FastMCP server for exposing openreview-py library structure."""

import logging
import os
import datetime
from typing import Any, Dict
from logging.handlers import RotatingFileHandler

from fastmcp import FastMCP, Context
from fastmcp.utilities.logging import get_logger
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware, RetryMiddleware

from src.introspect import (
    get_openreview_classes,
    get_openreview_functions,
    search_openreview_functions,
    get_library_overview
)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Generate timestamp for log file
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"logs/openreview_mcp_{timestamp}.log"

# Setup logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(process)d - %(thread)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        ),
        logging.FileHandler("openreview_mcp.log")  # Keep a current log file too
    ]
)

# Get FastMCP logger for server-side logging
logger = get_logger("openreview_mcp")

# Initialize FastMCP server
mcp = FastMCP(
    name="OpenReview Python Library MCP Server",
    instructions="MCP server that provides programmatic access to the openreview-py library structure and functionality",
    version="0.1.0"
)

# Note: @mcp.error_handler decorator is not available in FastMCP.
# Error handling is done through middleware instead (see ErrorHandlingMiddleware below)


@mcp.tool()
async def get_server_capabilities(ctx: Context) -> Dict[str, Any]:
    """
    Get information about this MCP server's capabilities and available tools.
    
    Returns:
        Dictionary containing server metadata, available tools and their descriptions
    """
    # Server-side logging
    logger.info("Retrieving server capabilities information")

    # Client-side logging
    await ctx.info("Requesting server capabilities")

    try:
        # Collect all tools metadata (get_tools returns list of tool names)
        tool_names = await mcp.get_tools()

        # Build capabilities response
        capabilities = {
            "server_info": {
                "name": mcp.name,
                "instructions": mcp.instructions,
                "version": mcp.version,
            },
            "tools": tool_names,
            "tool_count": len(tool_names),
            "timestamp": datetime.datetime.now().isoformat()
        }

        logger.info(f"Returning capabilities with {len(tool_names)} available tools")

        await ctx.info("Server capabilities retrieved successfully",
                     extra={"tool_count": len(tool_names)})

        return capabilities
    except Exception as e:
        logger.error(f"Error retrieving server capabilities: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to retrieve server capabilities: {str(e)}")
        raise


@mcp.tool()
async def list_openreview_functions(ctx: Context, filter_by_module: str = None) -> Dict[str, Any]:
    """
    Get a list of all available functions from the openreview-py library.
    
    Args:
        filter_by_module: Optional module name to filter functions (e.g., 'openreview.api')
        
    Returns:
        JSON array of functions with name, docstring, module, signature, and type
    """
    # Server-side logging
    logger.info(f"Listing OpenReview functions with filter: {filter_by_module}")

    # Client-side logging
    await ctx.info(f"Retrieving OpenReview functions",
                  extra={"filter_module": filter_by_module})

    try:
        functions = get_openreview_functions()

        # TODO: Implement more sophisticated filtering
        # - Filter by function type (constructor, method, function)
        # - Filter by parameter count or complexity
        # - Sort by relevance or alphabetical order
        if filter_by_module:
            functions = [f for f in functions if f.get("module") == filter_by_module]

        # Log the results
        logger.info(f"Found {len(functions)} functions matching criteria")

        await ctx.info(f"Found {len(functions)} functions",
                      extra={"count": len(functions)})

        # Standardize the response format
        return {
            "status": "success",
            "count": len(functions),
            "functions": functions,
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "filter": filter_by_module
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving functions: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to retrieve functions: {str(e)}")
        raise


@mcp.tool()
async def list_openreview_classes(ctx: Context, include_methods: bool = True) -> Dict[str, Any]:
    """
    Get a list of all available classes from the openreview-py library.
    
    Args:
        include_methods: Whether to include class methods in the response
        
    Returns:
        JSON array of classes with name, docstring, module, and optionally methods
    """
    # Server-side logging
    logger.info(f"Listing OpenReview classes with include_methods={include_methods}")

    # Client-side logging
    await ctx.info("Retrieving OpenReview classes",
                  extra={"include_methods": include_methods})

    try:
        classes = get_openreview_classes()

        # TODO: Add more filtering options:
        # - Filter by inheritance hierarchy
        # - Filter by class type (abstract, concrete, mixin)
        # - Include/exclude private methods
        # - Add property information
        if not include_methods:
            for cls in classes:
                cls.pop("methods", None)

        # Log the results
        method_count = sum(len(cls.get("methods", [])) for cls in classes if include_methods)
        logger.info(f"Found {len(classes)} classes with {method_count} methods")

        await ctx.info(f"Found {len(classes)} classes",
                      extra={
                          "class_count": len(classes),
                          "method_count": method_count if include_methods else 0
                      })

        # Standardize the response format
        return {
            "status": "success",
            "count": len(classes),
            "classes": classes,
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "include_methods": include_methods,
                "method_count": method_count if include_methods else 0
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving classes: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to retrieve classes: {str(e)}")
        raise


@mcp.tool()
async def search_openreview_api(query: str, ctx: Context) -> Dict[str, Any]:
    """
    Search for functions and classes by name or keyword in docstrings.
    
    Args:
        query: Search term to find in function/class names or documentation
        
    Returns:
        JSON array of matching functions and classes
    """
    # Server-side logging
    logger.info(f"Searching OpenReview API with query: '{query}'")

    # Client-side logging
    await ctx.info(f"Searching for '{query}'")

    try:
        # Parameter validation
        if not isinstance(query, str):
            error_msg = f"Expected query to be a string, got {type(query).__name__}"
            logger.error(error_msg)
            await ctx.error(error_msg)
            raise TypeError(error_msg)

        if not query or not query.strip():
            logger.warning("Empty search query received")
            await ctx.warning("Empty search query provided, returning empty results")
            return {"status": "success", "count": 0, "results": [], "metadata": {"timestamp": datetime.datetime.now().isoformat(), "query": query}}
        
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
        
        # Log the results
        logger.info(f"Found {len(matching_functions)} functions matching query '{query}'")

        await ctx.info(f"Found {len(matching_functions)} matching functions",
                      extra={
                          "query": query,
                          "match_count": len(matching_functions)
                      })

        # Standardize the response format
        return {
            "status": "success",
            "count": len(matching_functions),
            "results": matching_functions,
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "query": query
            }
        }
    except Exception as e:
        logger.error(f"Error searching API with query '{query}': {str(e)}", exc_info=True)
        await ctx.error(f"Search failed: {str(e)}")
        raise


@mcp.tool()
async def get_openreview_overview(ctx: Context) -> Dict[str, Any]:
    """
    Get a comprehensive overview of the entire openreview-py library structure.
    
    Returns:
        Dictionary containing functions, classes, modules, and statistics
    """
    # Server-side logging
    logger.info("Retrieving OpenReview library overview")

    # Client-side logging
    await ctx.info("Generating OpenReview library overview")
    await ctx.debug("This may take a moment as we collect comprehensive information about the library")

    try:
        overview = get_library_overview()

        # TODO: Add more comprehensive information:
        # - Recent changes and version history
        # - Usage examples for common patterns
        # - API endpoint mappings
        # - Error handling patterns
        # - Configuration options

        # Extract key statistics for logging
        func_count = len(overview.get("functions", []))
        class_count = len(overview.get("classes", []))
        module_count = len(overview.get("modules", []))

        # Server-side logging
        logger.info(f"Overview generated: {func_count} functions, {class_count} classes, {module_count} modules")

        # Client-side logging
        await ctx.info("Overview generation complete",
                      extra={
                          "function_count": func_count,
                          "class_count": class_count,
                          "module_count": module_count
                      })

        return overview
    except Exception as e:
        logger.error(f"Error generating library overview: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to generate library overview: {str(e)}")
        raise


@mcp.tool()
async def get_function_details(function_name: str, ctx: Context) -> Dict[str, Any]:
    """
    Get detailed information about a specific function.
    
    Args:
        function_name: Name of the function to get details for
        
    Returns:
        Detailed function information including parameters, return types, examples
    """
    # Server-side logging
    logger.info(f"Retrieving details for function: '{function_name}'")

    # Client-side logging
    await ctx.info(f"Looking up details for function '{function_name}'")

    try:
        # Parameter validation
        if not isinstance(function_name, str):
            error_msg = f"Expected function_name to be a string, got {type(function_name).__name__}"
            logger.error(error_msg)
            await ctx.error(error_msg)
            raise TypeError(error_msg)

        if not function_name:
            error_msg = "Empty function name provided"
            logger.warning(error_msg)
            await ctx.warning(error_msg)
            return {"error": error_msg}

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
                result = {
                    **func,
                    "parameters": [],  # TODO: Extract parameter info
                    "return_type": func.get("return_type", "unknown"),
                    "examples": [],  # TODO: Add usage examples
                    "related_functions": []  # TODO: Find related functions
                }

                # Log successful retrieval
                logger.info(f"Found function details for '{function_name}'")

                module = func.get("module", "unknown")
                signature = func.get("signature", "unknown")
                await ctx.info(f"Retrieved details for function '{function_name}'",
                              extra={
                                  "function_name": function_name,
                                  "module": module,
                                  "signature": signature
                              })

                return result

        # Function not found
        error_msg = f"Function '{function_name}' not found"
        logger.warning(error_msg)

        await ctx.warning(error_msg)

        return {"error": error_msg}
    except Exception as e:
        logger.error(f"Error retrieving function details: {str(e)}", exc_info=True)
        await ctx.error(f"Failed to retrieve function details: {str(e)}")
        raise


@mcp.custom_route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint for monitoring server availability."""
    return {
        "status": "healthy",
        "service": "openreview-mcp-server",
        "version": "0.1.0"
    }


def main():
    """Run the FastMCP server."""
    # TODO: Add configuration options:
    # - Custom port configuration
    # - Logging level settings
    # - Cache configuration for introspection results
    # - Module inclusion/exclusion filters
    # - Performance monitoring
    
    # Add advanced error handling middleware
    mcp.add_middleware(ErrorHandlingMiddleware(
        include_traceback=True,
        transform_errors=True
    ))

    # Add retry middleware for transient errors
    mcp.add_middleware(RetryMiddleware(
        max_retries=3
    ))

    # Log server startup
    logger.info("Starting OpenReview Python Library MCP Server")
    
    # Also print to console for user-friendly output
    print("Starting OpenReview Python Library MCP Server (HTTP mode)...")
    print("Available tools:")
    print("- get_server_capabilities: Get available tools and capabilities")
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
    
    logger.info(f"Server configured with host={host}, port={port}")

    try:
        logger.info(f"Starting HTTP server on {host}:{port}...")
        mcp.run(transport="http", host=host, port=port)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        print("\nServer stopped gracefully.")
    except Exception as e:
        logger.critical(f"Failed to start server: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
