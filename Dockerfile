FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts

RUN pip install --no-cache-dir ".[postgres]"

EXPOSE 8000

CMD ["uvicorn", "dq_impact_monitor.api:app", "--host", "0.0.0.0", "--port", "8000"]
