FROM python:3.12-slim AS base

RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --create-home appuser

WORKDIR /opt/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appuser /opt/app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
