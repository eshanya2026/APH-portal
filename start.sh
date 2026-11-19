#!/usr/bin/env bash
# ==============================================================================
# APH Hospital Intranet Portal - Startup Script (Python Engine)
# ==============================================================================

set -e

# Port series configuration: Default to 1111 2222 3000 (or override via arguments or $PORTS/$PORT)
PORTS="${*:-${PORTS:-${PORT:-1111 2222 3000}}}"
PRIMARY_PORT=$(echo $PORTS | awk '{print $1}')

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "🏥 Starting APH Hospital Intranet Server (Port Series: ${PORTS})"
echo "========================================================================"

# Gracefully terminate any previous process listening on these ports
for P in $PORTS 1234; do
    OLD_PID=$(lsof -ti :${P} 2>/dev/null || true)
    if [ -n "$OLD_PID" ]; then
        echo "⚠️  Found previous process running on port ${P} (PID: ${OLD_PID}). Stopping..."
        kill -15 $OLD_PID 2>/dev/null || true
        sleep 0.5
        kill -9 $OLD_PID 2>/dev/null || true
    fi
done

# Detect server host IP
HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$HOST_IP" ]; then
    HOST_IP="192.168.101.75"
fi

# Launch Python server detached in the background with configured port series
if command -v setsid >/dev/null 2>&1; then
    setsid python3 server.py ${PORTS} > server.log 2>&1 &
else
    nohup python3 server.py ${PORTS} > server.log 2>&1 &
fi
SERVER_PID=$!
disown $SERVER_PID 2>/dev/null || true

# Wait up to 5 seconds for the server to bind and start listening
STARTED=false
for i in {1..10}; do
    if lsof -ti :${PRIMARY_PORT} > /dev/null 2>&1; then
        STARTED=true
        break
    fi
    sleep 0.5
done

# Check if process is alive and port is listening
if [ "$STARTED" = true ] && ps -p $SERVER_PID > /dev/null; then
    echo "✅ APH Hospital Portal started successfully! (PID: ${SERVER_PID})"
    echo ""
    echo "🌐 Active Port Series Access URLs:"
    for P in $PORTS; do
        echo "   • Port ${P}: http://localhost:${P} | http://${HOST_IP}:${P} | http://192.168.101.75:${P}"
    done
    echo ""
    echo "📄 Logs: tail -f server.log"
    echo "🛑 To stop: ./stop.sh"
    echo "========================================================================"
else
    echo "❌ Failed to start APH Hospital Portal."
    echo "Check server.log for details:"
    tail -n 20 server.log
    exit 1
fi
