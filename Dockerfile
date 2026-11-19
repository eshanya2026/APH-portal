# ==============================================================================
# Adhiparasakthi Hospitals & Research Institute (APH) Intranet Portal
# Production Container Image (Python 3.11 Slim)
# ==============================================================================

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=1111

# Set work directory
WORKDIR /app

# Copy all project files, data directories, and cached documents
COPY . /app

# Ensure correct permissions
RUN chmod +x /app/server.py 2>/dev/null || true

# Expose hospital intranet port
EXPOSE 1111

# Health check to ensure the server is serving traffic
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:1111/', timeout=2)" || exit 1

# Launch hospital portal server on port 1111
CMD ["python3", "server.py", "1111"]

