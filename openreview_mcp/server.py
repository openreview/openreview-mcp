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
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
