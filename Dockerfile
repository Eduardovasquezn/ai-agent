# Base image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install the project into `/app`
WORKDIR /app

# Set environment variables (e.g., set Python to run in unbuffered mode)
ENV PYTHONUNBUFFERED 1

ENV PYTHONPATH=/app

# Install system dependencies for building libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependency management files (lock file and pyproject.toml) first
COPY uv.lock pyproject.toml /app/

# Install the application dependencies
RUN uv sync --frozen --no-cache

# Copy your application code into the container
COPY src/ /app/src
COPY config/ /app/config

# Set the virtual environment environment variables
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Install the package in editable mode
# RUN uv pip install -e .

# Expose the port
EXPOSE 8000

# Run the FastAPI app using uvicorn
CMD ["/app/.venv/bin/fastapi", "run", "src/core/app.py", "--port", "8000", "--host", "0.0.0.0"]
