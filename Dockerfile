# ── Base image ──────────────────────────────────────────────
FROM python:3.12-slim

# Azure Speech SDK needs libssl and libgomp
RUN apt-get update && apt-get install -y --no-install-recommends \
        libssl-dev \
        libffi-dev \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Install Python dependencies ──────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy source ───────────────────────────────────────────────
COPY app/ app/

# ── Runtime ───────────────────────────────────────────────────
EXPOSE 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
