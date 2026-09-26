FROM python:3.11-slim

# postgresql-client: 정기 백업(backup.py)이 pg_dump를 호출한다.
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data
COPY storage ./storage

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Render·Railway·Fly는 PORT 환경변수로 포트를 지정한다.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
