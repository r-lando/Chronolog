FROM python:3.12-slim

# System libraries required by WeasyPrint (PDF rendering) and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./alembic.ini .
COPY ./alembic ./alembic

# Evidence storage lives outside any directory that could ever be served
# statically or executed. It is only ever read/written via authenticated
# API code, never mapped as a static file root.
RUN mkdir -p /app/storage/evidence

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
