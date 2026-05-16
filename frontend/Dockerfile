FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY app/ app/

ENV PYTHONPATH=/app

EXPOSE 8501
CMD ["uv", "run", "--no-dev", "streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
