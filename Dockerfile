FROM python:3.12-slim

WORKDIR /app

# Install git (needed for openreview-py git dependency)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install the MCP server and its dependencies (including openreview-py from git)
RUN pip install --no-cache-dir .

# Default knowledge path inside the container
# Users mount their openreview-py clone to this path
ENV OPENREVIEW_KNOWLEDGE_PATH=/knowledge

# The MCP server uses stdio transport
ENTRYPOINT ["openreview-mcp"]
