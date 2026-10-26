# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python -m pip install \
        --no-cache-dir \
        --prefer-binary \
        --retries 10 \
        --timeout 120 \
        -r requirements.txt

COPY --from=website-builder /python /website-builder/python
COPY . .

EXPOSE 8000

CMD ["gunicorn", "pixelcore_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
