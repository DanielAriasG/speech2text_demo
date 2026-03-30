import whisper
import tempfile
import os
import torch
from backend.core.asr_interface import IASRModel

class WhisperModel(IASRModel):
    """
    Implementation using openai-whisper library.
    Defaulting to 'large-v3' as requested by the user.
    """
    def __init__(self, model_size: str = "large-v3"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Load model into memory/VRAM once.
        self.model = whisper.load_model(model_size, device=device)

    def transcribe(self, audio_data: bytes) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        try:
            # CPU doesn't support fp16 in many versions of whisper
            fp16 = torch.cuda.is_available()
            result = self.model.transcribe(tmp_path, fp16=fp16)
            return result.get("text", "").strip()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
