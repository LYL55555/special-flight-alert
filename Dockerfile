FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY python /app/python
COPY alert_engine/requirements.txt /app/alert_engine/requirements.txt

RUN grep -v '^\.\./' /app/alert_engine/requirements.txt > /tmp/requirements.docker.txt \
    && pip install --no-cache-dir -r /tmp/requirements.docker.txt \
    && pip install --no-cache-dir /app/python

COPY api /app/api
COPY alert_engine /app/alert_engine

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
