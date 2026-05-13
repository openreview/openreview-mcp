FROM python:3.12-slim

WORKDIR /app

# Install git (needed for openreview-py git dependency)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy and install MCP server
COPY pyproject.toml README.md ./
COPY openreview_mcp/ openreview_mcp/
RUN pip install --no-cache-dir .

# Knowledge files are bundled inside the package. To override with a live
# openreview-py clone, pass -e OPENREVIEW_KNOWLEDGE_PATH=/path at runtime.
EXPOSE 8080
ENTRYPOINT ["openreview-mcp"]
