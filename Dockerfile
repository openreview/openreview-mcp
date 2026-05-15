FROM python:3.12-slim

WORKDIR /app

# Install git (needed for the openreview-py git dependency and the upstream clone below)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Bake a shallow clone of upstream openreview-py into the image so that
# `search_test_examples` works out of the box — the tests/ directory is not
# shipped by `pip install openreview-py`. Force a fresh clone on rebuild with
# `docker build --no-cache`. Runtime callers can override the snapshot by
# bind-mounting their own checkout at /openreview-py.
RUN git clone --depth 1 https://github.com/openreview/openreview-py.git /openreview-py
ENV OPENREVIEW_KNOWLEDGE_PATH=/openreview-py

# Copy and install MCP server
COPY pyproject.toml README.md ./
COPY openreview_mcp/ openreview_mcp/
RUN pip install --no-cache-dir .

# best_practices.md is curated in this repo and bundled inside the package
# (the OPENREVIEW_KNOWLEDGE_PATH dir does not need to contain it — the loader
# falls back to the bundled copy). The env var above is set so the tests-index
# layer auto-discovers /openreview-py/tests/ at startup.
EXPOSE 8080
ENTRYPOINT ["openreview-mcp"]
