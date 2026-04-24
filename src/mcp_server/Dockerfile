FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN pip install uv && uv sync --no-dev
COPY src/ ./src/
CMD ["python", "-m", "src.mcp_server.server"]
