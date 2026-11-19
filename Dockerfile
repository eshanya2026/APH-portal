# ==============================================================================
# Adhiparasakthi Hospitals & Research Institute (APH) Intranet Portal
# Production Container Image (Python 3.11 Slim)
# ==============================================================================

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=1111 \
    PORTS="1111,2222,3000"

# Set work directory
WORKDIR /app

# Copy all project files, data directories, and cached documents
COPY . /app

# Ensure correct permissions
RUN chmod +x /app/server.py 2>/dev/null || true

# Expose hospital intranet port series (1111, 2222, 3000)
EXPOSE 1111 2222 3000

# Health check to ensure the server is serving traffic on primary port
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:1111/', timeout=2)" || exit 1

# Launch hospital portal server on the configured port series
CMD ["python3", "server.py", "1111", "2222", "3000"]

