#!/usr/bin/env bash
# ==============================================================================
# APH Hospital Intranet Portal - Stop Script (Node.js Engine)
# ==============================================================================

PORTS="${*:-${PORTS:-${PORT:-1111 2222 3000 1234}}}"

echo "========================================================================"
echo "🛑 Stopping APH Hospital Intranet Server on Port Series: ${PORTS}"
echo "========================================================================"

STOPPED=false

for P in $PORTS; do
    PIDS=$(lsof -ti :${P} 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo "Found listening process on port ${P} (PID: ${PIDS}). Terminating..."
        kill -15 $PIDS 2>/dev/null || true
        sleep 0.5
        kill -9 $PIDS 2>/dev/null || true
        STOPPED=true
    fi
    if lsof -ti :${P} >/dev/null 2>&1; then
        fuser -k -9 ${P}/tcp 2>/dev/null || true
        STOPPED=true
    fi
done

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
