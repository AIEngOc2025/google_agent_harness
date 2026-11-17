FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
# Install uv and sync dependencies
RUN pip install --no-cache-dir uv && uv sync --no-dev
CMD ["uv", "run", "python", "serve.py"]