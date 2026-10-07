#!/usr/bin/env bash
# Kaggle Startup Script for AI Movie Studio with Free Cloudflare Tunnel
set -e

export DEVICE="cuda"
export DTYPE="float16"
export ENABLE_CPU_OFFLOAD="false"
export ENABLE_VAE_TILING="true"
export ENABLE_VAE_SLICING="true"
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "=== Starting AI Movie Studio on Kaggle (T4 16GB) ==="
echo "CUDA Available: $(python -c 'import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")')"

# Build frontend if not built
if [ ! -d "frontend/dist" ]; then
    echo "Building frontend..."
    cd frontend && npm install && npm run build && cd ..
fi

mkdir -p logs

# Auto-install cloudflared if missing from PATH
if ! command -v cloudflared &> /dev/null; then
    echo "cloudflared not found. Downloading and installing Cloudflare Tunnel..."
    wget -q -O /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i /tmp/cloudflared.deb > /dev/null 2>&1 || true
    rm -f /tmp/cloudflared.deb
fi

# Kill any stale cloudflared instances from previous notebook runs
pkill -f cloudflared 2>/dev/null || true
sleep 1
rm -f logs/tunnel.log

echo "Starting Free Cloudflare Tunnel..."
cloudflared tunnel --url http://127.0.0.1:8000 --no-autoupdate > logs/tunnel.log 2>&1 &

# Persistent background watcher to catch and print URL the instant it is generated
(
    for i in {1..30}; do
        URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' logs/tunnel.log 2>/dev/null | head -n 1 || true)
        if [ -n "$URL" ]; then
            echo ""
            echo "=========================================================="
            echo "🎬 AI MOVIE STUDIO IS LIVE AT: $URL"
            echo "=========================================================="
            echo ""
            break
        fi
        sleep 1
    done
) &

# Synchronous wait up to 15 seconds to print URL before server logs
echo "Waiting for Cloudflare Tunnel URL..."
TUNNEL_URL=""
for i in {1..15}; do
    if [ -f logs/tunnel.log ]; then
        TUNNEL_URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' logs/tunnel.log | head -n 1 || true)
        if [ -n "$TUNNEL_URL" ]; then
            break
        fi
    fi
    sleep 1
done

echo "=========================================================="
if [ -n "$TUNNEL_URL" ]; then
    echo "🎬 AI MOVIE STUDIO IS LIVE AT: $TUNNEL_URL"
else
    echo "Cloudflare Tunnel is connecting in background..."
    echo "Watch for the URL in the output or run: cat logs/tunnel.log"
fi
echo "=========================================================="

# Run backend on port 8000
echo "Starting FastAPI backend server..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
