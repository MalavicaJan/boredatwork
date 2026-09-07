# Python 3.11 to match the venv this was developed against.
# The slim image is Debian-based and has ARM64 builds, which is what the
# Oracle Ampere instances run.
FROM python:3.11-slim

# Don't buffer stdout, or logs arrive late and out of order in
# `docker compose logs`.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Requirements first, so a code change doesn't reinstall every package.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations

# Runs as a non-root user: a container that never needs to write to its
# own filesystem shouldn't be able to.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
