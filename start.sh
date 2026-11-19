#!/usr/bin/env bash
# ==============================================================================
# APH Hospital Intranet Portal - Startup Script (Python Engine)
# ==============================================================================

set -e

# Port configuration: Default to 3000 (or override via argument or $PORT)
PORT="${1:-${PORT:-3000}}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "🏥 Starting APH Hospital Intranet Server (Python Engine) on Port: ${PORT}"
echo "========================================================================"

# Gracefully terminate any previous process listening on this port
OLD_PID=$(lsof -ti :${PORT} 2>/dev/null || true)
if [ -n "$OLD_PID" ]; then
    echo "⚠️  Found previous process running on port ${PORT} (PID: ${OLD_PID}). Stopping..."
    kill -15 $OLD_PID 2>/dev/null || true
    sleep 1
    kill -9 $OLD_PID 2>/dev/null || true
fi

# Detect server host IP
HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$HOST_IP" ]; then
    HOST_IP="192.168.101.75"
fi

# Launch Python server detached in the background
if command -v setsid >/dev/null 2>&1; then
    setsid python3 server.py "${PORT}" > server.log 2>&1 &
else
    nohup python3 server.py "${PORT}" > server.log 2>&1 &
fi
SERVER_PID=$!
disown $SERVER_PID 2>/dev/null || true

# Wait up to 5 seconds for the server to bind and start listening
STARTED=false
for i in {1..10}; do
    if lsof -ti :${PORT} > /dev/null 2>&1; then
        STARTED=true
        break
    fi
    sleep 0.5
done

# Check if process is alive and port is listening
if [ "$STARTED" = true ] && ps -p $SERVER_PID > /dev/null; then
    echo "✅ APH Hospital Portal started successfully! (PID: ${SERVER_PID})"
    echo ""
    echo "🌐 Access URLs:"
    echo "   • Localhost:       http://localhost:${PORT}"
    echo "   • Hospital LAN:    http://${HOST_IP}:${PORT}"
    echo "   • Intranet Host:   http://192.168.101.75:${PORT}"
    echo ""
    echo "📄 Logs: tail -f server.log"
    echo "🛑 To stop: ./stop.sh (or: fuser -k ${PORT}/tcp)"
    echo "========================================================================"
else
    echo "❌ Failed to start APH Hospital Portal."
    echo "Check server.log for details:"
    tail -n 20 server.log
    exit 1
fi
