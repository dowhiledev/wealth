FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install Node.js (for building/serving Next.js UI) and system deps
RUN apt-get update -y \
    && apt-get install -y curl gnupg ca-certificates build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python project files
COPY pyproject.toml uv.lock* README.md LICENSE CONTRIBUTING.md ./
COPY src ./src

# Install Python package
RUN pip install --upgrade pip setuptools wheel \
    && pip install .

# Build UI once during image build to avoid runtime builds
WORKDIR /app/src/wealth_os/ui
RUN npm install --silent \
    && npm run build

WORKDIR /app

EXPOSE 8001 3000

# Run API + production UI. Bind on 0.0.0.0 and port 3000 for UI.
CMD ["wealth", "ui", "--ui-port", "3000", "--api-host", "0.0.0.0"]

