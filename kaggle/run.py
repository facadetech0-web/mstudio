import os
import sys
import time
import re
import subprocess
from pathlib import Path

# Set environment defaults for Kaggle T4
os.environ["DEVICE"] = "cuda"
os.environ["DTYPE"] = "float16"
os.environ["ENABLE_CPU_OFFLOAD"] = "false"
os.environ["ENABLE_VAE_TILING"] = "true"
os.environ["ENABLE_VAE_SLICING"] = "true"
os.environ["PYTHONPATH"] = f"{os.getcwd()}:{os.environ.get('PYTHONPATH', '')}"

print("=" * 60)
print("🎬 INITIALIZING AI MOVIE STUDIO ON KAGGLE (T4 16GB)")
print("=" * 60)

# 1. Check/Install Cloudflare Tunnel
Path("logs").mkdir(exist_ok=True)
tunnel_log_path = Path("logs/tunnel.log")

cloudflared_installed = subprocess.run(["which", "cloudflared"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
if not cloudflared_installed:
    print("Installing Cloudflare Tunnel (cloudflared)...")
    subprocess.run(
        "wget -q -O /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && dpkg -i /tmp/cloudflared.deb && rm -f /tmp/cloudflared.deb",
        shell=True
    )

# 2. Terminate any previous tunnel/uvicorn processes
subprocess.run("pkill -f cloudflared", shell=True, stderr=subprocess.DEVNULL)
subprocess.run("pkill -f 'uvicorn backend.main:app'", shell=True, stderr=subprocess.DEVNULL)
if tunnel_log_path.exists():
    tunnel_log_path.unlink()

time.sleep(1)

# 3. Start Cloudflare Tunnel in background
print("Starting Cloudflare Tunnel...")
tunnel_log = open(tunnel_log_path, "w", buffering=1)
tunnel_proc = subprocess.Popen(
    ["cloudflared", "tunnel", "--url", "http://127.0.0.1:8000", "--no-autoupdate"],
    stdout=tunnel_log,
    stderr=subprocess.STDOUT
)

# 4. Wait for tunnel URL and display it
print("Connecting to Cloudflare network...")
tunnel_url = None
for _ in range(20):
    time.sleep(1)
    if tunnel_log_path.exists():
        content = tunnel_log_path.read_text(errors="ignore")
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
        if match:
            tunnel_url = match.group(0)
            break

print("")
print("*" * 64)
if tunnel_url:
    print(f"🎉 STUDIO IS ONLINE: {tunnel_url}")
    print(f"👉 CLICK TO OPEN:    {tunnel_url}")
    try:
        from IPython.display import display, HTML
        display(HTML(f'''
            <div style="background:#111; padding:20px; border-radius:10px; border:2px solid #f59e0b; margin:15px 0;">
                <h2 style="color:#f59e0b; margin:0 0 10px 0;">🎬 AI MOVIE STUDIO IS LIVE!</h2>
                <a href="{tunnel_url}" target="_blank" style="display:inline-block; background:#f59e0b; color:#111; padding:10px 20px; font-size:16px; font-weight:bold; border-radius:6px; text-decoration:none;">
                    👉 Open Studio: {tunnel_url}
                </a>
            </div>
        '''))
    except Exception:
        pass
else:
    print("Cloudflare Tunnel is starting. Check logs/tunnel.log for the URL.")
print("*" * 64)
print("")

# 5. Launch FastAPI / Uvicorn server in foreground
print("Starting FastAPI Backend Server on port 8000...")
sys.stdout.flush()

try:
    subprocess.run([
        sys.executable, "-m", "uvicorn", "backend.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
finally:
    tunnel_proc.terminate()
    tunnel_log.close()
