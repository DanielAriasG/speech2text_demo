FROM python:3.11-slim

# Install system dependencies
# ffmpeg is essential for native torchaudio / Whisper fallback operations
RUN apt-get update && \
    apt-get install -y ffmpeg libsndfile1 git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code logs and tests
COPY . .

EXPOSE 8000
ENV PYTHONPATH=/app

# Start FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
