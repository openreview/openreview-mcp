#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Copy tools plugin if sibling directory exists
if [ -d "$PARENT_DIR/openreview-tools-mcp" ]; then
    echo "Found openreview-tools-mcp, including in build..."
    cp -r "$PARENT_DIR/openreview-tools-mcp" "$SCRIPT_DIR/tools-plugin"
else
    echo "No openreview-tools-mcp found, building without tools plugin."
fi

docker build -t openreview-mcp "$SCRIPT_DIR"

# Clean up
rm -rf "$SCRIPT_DIR/tools-plugin"

echo ""
echo "Done. Run with:"
echo "  docker run --rm -i -v /path/to/openreview-py:/knowledge openreview-mcp"
