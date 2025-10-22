# Multi-stage build for Google Drive Sync Tool
# Stage 1: Builder
FROM python:3.11-slim as builder

# Set metadata
LABEL stage=builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies to user directory
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim as production

# Set metadata
LABEL maintainer="your-email@example.com" \
      description="Google Drive Synchronisation Tool" \
      version="1.0.0" \
      org.opencontainers.image.source="https://github.com/yourusername/gdrive-sync"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    GDRIVE_DATA_DIR=/data \
    GDRIVE_CONFIG_DIR=/config \
    GDRIVE_DOWNLOAD_DIR=/downloads

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    wget \
    curl \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 gdrive && \
    useradd -m -u 1000 -g gdrive -s /bin/bash gdrive && \
    mkdir -p /data /config /downloads /app && \
    chown -R gdrive:gdrive /data /config /downloads /app

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder --chown=gdrive:gdrive /root/.local /home/gdrive/.local

# Copy application code
COPY --chown=gdrive:gdrive main.py ./
COPY --chown=gdrive:gdrive gdrive_sync/ ./gdrive_sync/
COPY --chown=gdrive:gdrive config_examples/ ./config_examples/
COPY --chown=gdrive:gdrive .gdriveignore ./

# Copy Docker specific files
COPY --chown=gdrive:gdrive docker/entrypoint.sh /entrypoint.sh
COPY --chown=gdrive:gdrive docker/healthcheck.sh /healthcheck.sh
RUN chmod +x /entrypoint.sh /healthcheck.sh

# Update PATH
ENV PATH=/home/gdrive/.local/bin:$PATH

# Switch to non-root user
USER gdrive

# Create volume mount points
VOLUME ["/data", "/config", "/downloads"]

# Expose port for OAuth callback
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ["/healthcheck.sh"]

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command (interactive mode)
CMD ["python", "main.py"]

# Stage 3: Development
FROM production as development

# Switch back to root for installations
USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    nano \
    less \
    bash-completion \
    && rm -rf /var/lib/apt/lists/*

# Copy dev requirements
COPY requirements-dev.txt /tmp/

# Install dev dependencies
RUN pip install --no-cache-dir -r /tmp/requirements-dev.txt

# Switch back to gdrive user
USER gdrive

# Override command for development
CMD ["bash"]
