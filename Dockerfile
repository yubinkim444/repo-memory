FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install .

# Default to stdio MCP server; mount your repo at /repo and set REPO_MEMORY_ROOT.
ENV REPO_MEMORY_ROOT=/repo
ENTRYPOINT ["repo-memory-mcp"]
