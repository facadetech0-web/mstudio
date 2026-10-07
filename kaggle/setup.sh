# Kaggle Setup Script for AI Movie Studio (NVIDIA T4 16GB VRAM)
# Run in Kaggle Notebook Terminal or as code cell: !bash kaggle/setup.sh
set -e

echo "=== [1/5] Checking GPU Environment ==="
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi
else
    echo "Notice: nvidia-smi command not found. Ensure Accelerator: GPU T4 x2 or GPU T4 is enabled in the right panel of your Kaggle notebook."
fi

echo "=== [2/5] Installing System Dependencies (FFmpeg & Cloudflare Tunnel) ==="
apt-get update -qq || true
apt-get install -y -qq --fix-missing ffmpeg wget curl || true

if ! command -v cloudflared &> /dev/null; then
    echo "Downloading and installing Cloudflare Tunnel (cloudflared)..."
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i cloudflared-linux-amd64.deb
    rm -f cloudflared-linux-amd64.deb
fi

echo "=== [3/5] Installing Python Dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [4/5] Preparing Directories ==="
mkdir -p models outputs projects logs

echo "=== [5/5] Setup Complete ==="
echo "You can now run: bash kaggle/start.sh"
