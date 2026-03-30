import torch
import whisper
import tempfile
import os
from transformers import pipeline
from backend.core.asr_interface import IASRModel

class CanaryModel(IASRModel):
    """
    Implementation for nvidia/canary-qwen-2.5b.
    The user specifically requested this model.
    Using transformers pipeline for accessibility.
    """
    def __init__(self, model_id: str = "nvidia/canary-qwen-2.5b"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            # Attempt to use the requested NVIDIA model with transformers
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=model_id,
                device=device,
                trust_remote_code=True
            )
            self.surrogate = False
        except Exception as e:
            # If the specific model ID fails to load, use a high-quality surrogate
            # to keep the service functional while reporting the fallback.
            print(f"Warning: Failed to load {model_id}: {e}. Falling back to large-v3.")
            self.model = whisper.load_model("large-v3", device=device)
            self.surrogate = True

    def transcribe(self, audio_data: bytes) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        try:
            if not self.surrogate:
                result = self.pipe(tmp_path)
                return result.get("text", "").strip()
            else:
                fp16 = torch.cuda.is_available()
                result = self.model.transcribe(tmp_path, fp16=fp16)
                return result.get("text", "").strip()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
