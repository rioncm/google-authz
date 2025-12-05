# --- Base image with Python runtime ---
FROM python:3.12-slim AS base

# Set workdir inside the container
WORKDIR /app

# Avoid Python bytecode / buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system packages needed by pip & runtime
# (curl just for debugging; you can drop it if you like)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# --- Dependencies layer ---
FROM base AS deps

# Copy only requirements to leverage Docker layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# --- Runtime image ---
FROM base AS runtime

# Create a non-root user
RUN useradd -m appuser

# Copy installed Python packages from deps layer
COPY --from=deps /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy the application code
COPY . /app

# Make sure we run as non-root
USER appuser

# Expose the port your app listens on
EXPOSE 8000

# ENV for Google creds
# At runtime you'll mount the JSON key to this path
# e.g. docker run -v /path/to/sa.json:/secrets/sa.json:ro -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json ...
ENV GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json

# Optional: other envs
# ENV GOOGLE_ADMIN_DELEGATED_USER=admin@pminc.me
# ENV APP_ENV=production

# Start the app with Gunicorn + Uvicorn worker
# Adjust "app.main:app" to your actual module:app
CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "60"]