# Modular ASR Platform

A full-stack architecture that transforms live audio components into multi-colored UI document spaces! By harnessing OpenAI Whisper alongside Pyannote Diarization architectures, it seamlessly provides Live Microphone Dictation and Multi-Format (DOCX/PDF) Document transcription chunks.

---

## 🛠 Prerequisites

Ensure you have the following installed locally on your system:
- **Python 3.11** (Must be `>=3.10` and `<3.14`. Python 3.14+ is currently unsupported by core audio dependencies like `numba`).
- **Node.js 20+**
- **FFMPEG** (Required down path natively if running non-Docker)
- A valid **HuggingFace API Token** (`HF_TOKEN`) mapped to the `pyannote/speaker-diarization-3.1` model terms agreement.

---

## 💻 Local Installation & Setup

If you prefer to run the API endpoints and Frontend React logic natively on your host machine without Docker, follow these explicit instructions.

### 1. Backend API (Python)
The entire heavy-lifting inference models are executed under FastAPI.
```bash
# Move into root
cd "ASR Platform"

# Initialize Virtual Environment
python3.11 -m venv venv

# Activate Environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
# --- GPU Acceleration Setup (For CUDA 13.1+) ---
# If you are using an NVIDIA GPU with CUDA 13.1+, perform a clean 
# reinstallation of the Torch stack to ensure GPU visibility:
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130

# Verify successful GPU registration
python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"

# Install strictly tracked dependencies
pip install -r requirements.txt



# Store your gated authentication Token
# Windows:
$env:HF_TOKEN="your_hf_token_here"
# Mac/Linux:
export HF_TOKEN="your_hf_token_here"

# Spin up FastAPI locally!
uvicorn backend.main:app --reload
```

### 2. Frontend UI (React)
A stunning modular Vite deployment serving websockets.
```bash
cd frontend

# Install UI modules
npm install

# Build UI loop
npm run dev
```

The Web Application will instantly mount on `http://localhost:5173`.

---

## 🐳 Docker Deployment

The ecosystem contains an optimized unified Docker Compose network capable of passthrough GPU execution!

```bash
# Pass your gated HF token into the container architecture inline!
HF_TOKEN="your_hf_token_code" docker-compose up --build
```
* **Frontend**: Available immediately at `http://localhost:5173`
* **Backend**: Available immediately at `http://localhost:8000`

---

## 📊 Run STT Benchmark Tooling

Want to benchmark the inference algorithms across the 10-sample HuggingFace Test Suite natively? We've programmed an isolated script designed to mimic the pipecat-ai logic and return exact TTFS Latencies plus Acoustic Werner errors! Ensure your python backend environment is active, then execute:

```bash
python tests/stt_benchmark_runner.py
```
This script intelligently extracts raw byte-stream chunks from PyArrow structures directly avoiding SubProcess FFMPEG decoding complications and safely logs the evaluation parameters!
