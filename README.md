# AI Movie Studio

**AI Movie Studio** is an advanced full-stack AI cinematic production suite designed specifically to run efficiently on a **free Kaggle NVIDIA T4 (16GB VRAM) GPU**.

It transforms high-level movie ideas into multi-scene, multi-shot cinematic productions by leveraging **OpenRouter as the AI Director / Script Supervisor** for narrative decomposition and continuity, **CogVideoX-2B for fast preview generation**, **CogVideoX-5B-I2V for final image-to-video rendering**, and **FFmpeg** for final resolution-normalized assembly.

---

## 🌟 Core Concepts & Architectural Principles

1. **One User Prompt ≠ One Single Video**:
   Instead of generating a single short video, the AI Director decomposes the narrative into sequential, logically progressive scenes, shots, and clips.
2. **OpenRouter = AI Director (Intelligence Only)**:
   OpenRouter is never used for video rendering. It manages story architecture, Movie Bibles, character/wardrobe consistency, location lighting, camera motion planning, and multi-clip continuity plans.
3. **Dual-Model Generation Tier**:
   - **CogVideoX-2B**: Fast, resource-friendly preview generation for prompt and camera validation.
   - **CogVideoX-5B-I2V**: High-fidelity final render using reference image anchoring.
4. **Independent Clip Approval & Regeneration**:
   Any clip in the timeline can be independently rejected and regenerated with custom feedback without re-rendering the surrounding clips.
5. **Strict T4 16GB Memory Budgeting**:
   Sequential CPU offloading, FP16 half-precision, VAE tiling, VAE slicing, dynamic CUDA cache cleanup, and single-model VRAM residency ensure zero unhandled Out-Of-Memory (OOM) crashes.

---

## 🏗️ Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        React + TypeScript + Vite                       │
│     (Dark Cinema UI, Timeline, Clips Slider, AI Director Hub)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / SSE Stream
┌───────────────────────────────────▼────────────────────────────────────┐
│                             FastAPI Backend                            │
├────────────────────┬───────────────────┬───────────────────────────────┤
│   AI Director      │   Video Models    │        Background Queue       │
│  (OpenRouter API)  │  CogVideoX 2B/5B  │       (Job State, Peak VRAM)  │
├────────────────────┴───────────────────┴───────────────────────────────┤
│          SQLite DB  +  FFmpeg Normalization & Concat Pipeline          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```text
movie-studio/
│
├── frontend/                     # React + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/           # TopBar, Sidebar, PreviewPlayer, Timeline, etc.
│   │   ├── api/client.ts         # API integration client
│   │   ├── types.ts              # Schema interfaces
│   │   └── App.tsx               # Studio workspace entry
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                      # FastAPI Python Backend
│   ├── api/                      # Endpoints: projects, scenes, shots, clips, jobs, system
│   ├── database/                 # SQLite session & tables
│   ├── models/                   # SQLAlchemy DB models
│   ├── schemas/                  # Pydantic structured schemas
│   ├── services/
│   │   ├── ai/                   # OpenRouter Director & Prompt Enhancer
│   │   ├── video/                # ModelManager, CogVideoX2B, CogVideoX5BI2V
│   │   ├── ffmpeg/               # Movie normalization & concat pipeline
│   │   └── queue/                # Sequential GPU job worker
│   ├── config.py                 # Configuration loader
│   ├── logging_config.py         # Masked logger (No key leaks)
│   └── main.py                   # FastAPI server entry
│
├── kaggle/                       # Kaggle T4 Deployment
│   ├── setup.sh                  # Setup script for Kaggle environment
│   └── start.sh                  # Application launcher
│
├── tests/                        # Backend & E2E Pytest test suite
├── models/                       # Local model weights directory
├── projects/                     # Persistent projects, bibles, and exports
├── outputs/                      # Generated video clips
├── logs/                         # Structured application logs
├── .env.example                  # Environment configuration template
├── requirements.txt              # Backend dependencies
└── README.md
```

---

## 🚀 Kaggle T4 Deployment Guide

> **Note**: This project targets **Kaggle NVIDIA T4 (16GB VRAM)**. Do not use Google Colab.

### 1. In Kaggle Notebook Settings
1. Set **Accelerator** to **GPU T4 x2** or **GPU T4**.
2. Enable **Internet Access: On**.

### 2. Run Setup
In a Kaggle terminal or notebook code cell:
```bash
!bash kaggle/setup.sh
```

### 3. Launch the Application with Free Cloudflare Tunnel
```bash
!bash kaggle/start.sh
```
`start.sh` automatically launches the built-in **Free Cloudflare Tunnel** and prints your public URL:
```text
==========================================================
🎬 AI MOVIE STUDIO IS LIVE AT: https://random-name.trycloudflare.com
==========================================================
```
No account, signup, or auth token is required! Open the URL directly in any browser.

---

## 💻 Local Setup & Development

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- FFmpeg installed (`apt-get install ffmpeg` on Ubuntu/Debian, or via Windows package manager)
- NVIDIA GPU with CUDA (optional for development; offline mock-free validation operates automatically)

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Set your OpenRouter API key:
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

### 3. Run Backend
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run Frontend
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🎬 Complete User Workflow

1. **Create Project**: Enter project title and select genre (e.g. *Sci-Fi Mystery*).
2. **AI Director Movie Planning**:
   - Enter your high-level movie premise (e.g., *"A man enters an abandoned factory, walks through it, discovers an old machine and turns it on"*).
   - Click **AI DIRECTOR** -> **Generate Full Movie Plan**.
   - The AI Director creates a comprehensive **Movie Bible**, locks character wardrobe (e.g., *worn black leather jacket*) and lighting styles, and creates structured scenes.
3. **Multi-Clip Decomposition (Core Feature)**:
   - Select a scene.
   - Adjust the **Number of Clips Slider** (e.g., `5 Clips`) and **Clip Duration** (`5 seconds`).
   - The UI displays `Estimated Total: ≈ 25 seconds`.
   - Click **AI Decompose into 5 Sequential Clips**.
   - The AI generates 5 logically progressive shots (Establishing shot -> Entering entrance -> Walking interior -> Discovering machine -> Activating machine).
4. **Preview Generation**:
   - Click **Generate Preview (CogVideoX-2B)**.
   - The job is queued in the background worker. Progress updates live in the queue drawer with step counts (e.g., `Step 18/25 (72%)`).
5. **Review & Independent Regeneration**:
   - Watch the rendered preview in the cinema viewport.
   - Click **Approve Clip** for Clip 1.
   - If Clip 2 needs adjustment, click **Reject**, add feedback (e.g., *"Make camera tracking slower"*), and click **Regenerate Single Clip**.
   - Only Clip 2 re-renders; Clips 1, 3, 4, and 5 are completely preserved.
6. **Final Rendering (CogVideoX-5B-I2V)**:
   - Upload or select a reference frame.
   - Click **Generate Final (CogVideoX-5B-I2V)**.
   - The 5B model synthesizes high-fidelity motion anchored to the reference image.
7. **Timeline Editing & Reordering**:
   - Use the bottom timeline to inspect all clips across scenes.
   - Reorder clips with the arrow controls or drag-and-drop.
8. **Export Final Movie**:
   - Click **Export Movie**.
   - The FFmpeg service normalizes each approved clip to standard resolution (720p/1080p), aligns frame rate (24 FPS), injects silent audio tracks, and produces a seamless final `movie.mp4`.

---

## ⚡ NVIDIA T4 16GB Memory Optimizations

To operate CogVideoX-5B within a 16GB VRAM budget without OOM errors, the backend applies:
- **Sequential CPU Offloading**: Moves transformer blocks to host RAM sequentially when executing layers.
- **FP16 Half-Precision**: Cuts model memory footprint in half.
- **VAE Tiling & Slicing**: Decodes video latents in tiles rather than all at once.
- **Single-Model Residency**: The `ModelManager` immediately unloads preview weights before loading final rendering weights.
- **CUDA Cache Eviction**: Invokes `torch.cuda.empty_cache()` and `gc.collect()` before and after generation passes.

### OOM Fallback
If an unexpected CUDA Out-Of-Memory error occurs, the worker intercepts the failure and displays:
```text
GPU memory is insufficient for this configuration. [Retry in Low VRAM Mode]
```
Clicking **Retry in Low VRAM Mode** automatically enables sequential offloading and reduces batch resolution.

---

## 📊 Hardware Benchmarking (Real Measurements Only)

Click **Benchmark** on the top bar to measure real GPU performance:
- Tests actual inference passes for `cogvideox-2b` and `cogvideox-5b-i2v`.
- Measures exact **Generation Time (seconds)** and **Peak VRAM (MB)** using `torch.cuda.max_memory_allocated()`.
- Stores results in the SQLite `benchmarks` table.
- **No simulated or fake benchmark numbers.**

---

## 🧪 Testing

Run backend unit and end-to-end integration tests:
```bash
python -m pytest tests/ -v
```

---

## 🔒 Security & Safe Operations
- OpenRouter API keys are stored exclusively in the backend environment and never transmitted to the client.
- Sensitive credentials and keys are automatically masked in all log outputs (`logs/api.log`, `logs/generation.log`).
- Strict validation of file uploads, paths, and structured JSON outputs prevents directory traversal and injection.
