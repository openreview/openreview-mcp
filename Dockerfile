FROM python:3.12-slim

WORKDIR /app

# Install git (needed for openreview-py git dependency)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy and install MCP server
COPY pyproject.toml README.md ./
COPY openreview_mcp/ openreview_mcp/
RUN pip install --no-cache-dir .

# Install tools plugin if present (optional)
# To include it: cp -r ../openreview-tools-mcp tools-plugin
# Then build normally: docker build -t openreview-mcp .
# Without it, the image works fine — just no live API tools.
COPY tools-plugi[n] /tmp/tools-plugin/
RUN if [ -f /tmp/tools-plugin/pyproject.toml ]; then \
        pip install --no-cache-dir /tmp/tools-plugin/ && \
        echo "openreview-tools-mcp plugin installed"; \
    else \
        echo "No tools plugin found, skipping"; \
    fi && rm -rf /tmp/tools-plugin

# Knowledge files are bundled inside the package. To override with a live
# openreview-py clone, pass -e OPENREVIEW_KNOWLEDGE_PATH=/path at runtime.
ENTRYPOINT ["openreview-mcp"]
