#!/usr/bin/env bash
# Kaggle Startup Script for AI Movie Studio with Free Cloudflare Tunnel
set -e

export DEVICE="cuda"
export DTYPE="float16"
export ENABLE_CPU_OFFLOAD="true"
export ENABLE_VAE_TILING="true"
export ENABLE_VAE_SLICING="true"

echo "=== Starting AI Movie Studio on Kaggle (T4 16GB) ==="
echo "CUDA Available: $(python -c 'import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None")')"

# Build frontend if not built
if [ ! -d "frontend/dist" ]; then
    echo "Building frontend..."
    cd frontend && npm install && npm run build && cd ..
fi

mkdir -p logs

# Start Free Cloudflare Tunnel in background (No account, token, or signup needed)
if command -v cloudflared &> /dev/null; then
    echo "Starting Free Cloudflare Tunnel..."
    cloudflared tunnel --url http://127.0.0.1:8000 --no-autoupdate > logs/tunnel.log 2>&1 &
    
    # Wait for tunnel URL generation
    echo "Waiting for Cloudflare Tunnel URL..."
    for i in {1..15}; do
        TUNNEL_URL=$(grep -o 'https://[-a-zA-Z0-9.]*\.trycloudflare\.com' logs/tunnel.log | head -n 1 || true)
        if [ -n "$TUNNEL_URL" ]; then
            break
        fi
        sleep 1
    done

    echo "=========================================================="
    if [ -n "$TUNNEL_URL" ]; then
        echo "🎬 AI MOVIE STUDIO IS LIVE AT: $TUNNEL_URL"
    else
        echo "Cloudflare Tunnel log:"
        cat logs/tunnel.log
    fi
    echo "=========================================================="
else
    echo "Notice: cloudflared not found in PATH. Install via bash kaggle/setup.sh"
fi

# Run backend on port 8000
echo "Starting FastAPI backend server..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
