"""Standalone FastMCP server entry point for openreview-mcp."""

import logging
import os

from fastmcp import FastMCP

from openreview_mcp.registration import register_knowledge_tools

logger = logging.getLogger("openreview_mcp")

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


# --- Plugin: live API tools (optional) ---
# Preserved as-is for Task 6 to delete. Do not remove in this task.
try:
    from openreview_tools import register_tools

    if os.environ.get("OPENREVIEW_API_TOKEN"):
        register_tools(mcp)
        logger.info("Registered openreview-tools-mcp live API tools")
except ImportError:
    pass


def main() -> None:
    """Start the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
