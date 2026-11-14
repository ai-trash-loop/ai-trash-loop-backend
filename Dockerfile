FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN useradd -m app
WORKDIR /srv
COPY pyproject.toml ./
COPY app ./app
# The engine is a separate repo/package; installed from GitHub (pin a tag/commit for reproducible builds).
RUN pip install --no-cache-dir "trashloop @ git+https://github.com/ai-trash-loop/ai-trash-loop-engine.git@main" . 
USER app
EXPOSE 8000
CMD ["uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
