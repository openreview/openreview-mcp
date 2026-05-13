"""Standalone FastMCP server entry point for openreview-mcp."""

from fastmcp import FastMCP

from openreview_mcp.registration import register_knowledge_tools

mcp = FastMCP(
    name="OpenReview Python Library Expert",
    instructions=(
        "Expert assistant for the openreview-py Python library. "
        "Use these tools to find API methods, best practices, code examples, "
        "and workflow guides for building with OpenReview."
    ),
)

# Register the 5 knowledge tools onto this server's FastMCP instance.
# Uses the bundled knowledge files unless OPENREVIEW_KNOWLEDGE_PATH overrides.
register_knowledge_tools(mcp)


def main() -> None:
    """Start the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="OpenReview MCP Server")
    parser.add_argument(
        "--transport", default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port", type=int, default=8080,
        help="Port for SSE/HTTP transport (default: 8080)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="Host for SSE/HTTP transport (default: 0.0.0.0)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
