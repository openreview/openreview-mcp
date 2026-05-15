FROM python:3.12-slim

WORKDIR /app

# Install git (needed for the openreview-py git dependency and the optional clone below)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Optionally bake a shallow clone of upstream openreview-py into the image so
# `search_test_examples` works out of the box on hosts that can't bind-mount
# a local checkout (Cloud Run, App Engine, etc.). Default is OFF — the typical
# local-Docker workflow is to bind-mount a local openreview-py at
# `/openreview-py` at runtime (every openreview developer already has a clone).
#
# Enable with:
#   docker build --build-arg CLONE_OPENREVIEW_PY=true -t openreview-mcp .
ARG CLONE_OPENREVIEW_PY=false
RUN if [ "$CLONE_OPENREVIEW_PY" = "true" ]; then \
      git clone --depth 1 https://github.com/openreview/openreview-py.git /openreview-py; \
    fi

# Set unconditionally — the resolvers in registration.py gracefully handle a
# missing /openreview-py directory (best_practices.md falls back to bundled;
# search_test_examples returns a disabled message). A runtime bind-mount at
# /openreview-py transparently fills in the tests dir for the lean image.
ENV OPENREVIEW_KNOWLEDGE_PATH=/openreview-py

# Copy and install MCP server
COPY pyproject.toml README.md ./
COPY openreview_mcp/ openreview_mcp/
RUN pip install --no-cache-dir .

EXPOSE 8080
ENTRYPOINT ["openreview-mcp"]
