#!/usr/bin/env bash
# ==============================================================================
# APH Hospital Intranet Portal - Stop Script (Node.js Engine)
# ==============================================================================

PORT="${1:-${PORT:-3000}}"

echo "========================================================================"
echo "🛑 Stopping APH Hospital Intranet Server on Port: ${PORT}"
echo "========================================================================"

STOPPED=false

# 1. Kill by port via lsof
PIDS=$(lsof -ti :${PORT} 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "Found listening process on port ${PORT} (PID: ${PIDS}). Terminating..."
    kill -15 $PIDS 2>/dev/null || true
    sleep 1
    kill -9 $PIDS 2>/dev/null || true
    STOPPED=true
fi

# 2. Kill by port via fuser if still listening
if lsof -ti :${PORT} >/dev/null 2>&1; then
    fuser -k -9 ${PORT}/tcp 2>/dev/null || true
    STOPPED=true
fi

# 3. Kill any lingering node server.js process
NODE_PIDS=$(pgrep -f "node server.js" 2>/dev/null || true)
if [ -n "$NODE_PIDS" ]; then
    kill -9 $NODE_PIDS 2>/dev/null || true
    STOPPED=true
fi

# Verify port is released
sleep 0.5
if ! lsof -ti :${PORT} >/dev/null 2>&1; then
    echo "✅ Server successfully stopped. Port ${PORT} is now free."
else
    echo "⚠️ Warning: Port ${PORT} might still be in use."
fi
echo "========================================================================"
