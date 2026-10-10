FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/src
CMD ["uvicorn", "travis.api.main:app", "--host", "0.0.0.0", "--port", "8000"]