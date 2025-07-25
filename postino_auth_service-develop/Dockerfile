# syntax=docker/dockerfile:1

#########################
# 1) Builder stage
#########################
FROM python:3.12-bookworm AS builder

# Disable .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build tools (for any C extensions)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only prod.requirements.txt first (to leverage caching)
COPY prod.requirements.txt .

# Install Python dependencies into /install
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r prod.requirements.txt

# Copy entire application code
COPY . .

#########################
# 2) Final stage
#########################
FROM python:3.12-bookworm

# Disable .pyc files, enable unbuffered logging,
# add /install/bin to PATH so 'gunicorn' is found,
# and include /install/lib/python3.12/site-packages in PYTHONPATH
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.12/site-packages:/app"

# Create a non-root user and group
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed dependencies from the builder
COPY --from=builder /install /install

# Copy application code from the builder
COPY --from=builder /app /app

# Fix ownership so that 'appuser' owns both /install and /app
RUN chown -R appuser:appgroup /install \
    && chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose port 5001 (Gunicorn/Uvicorn will bind here)
EXPOSE 5001

# ─── Point Gunicorn at src.main:app, binding to port 5001 ───
CMD ["gunicorn", "src.main:app", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:5001", \
     "--workers", "4", \
     "--log-level", "info"]
