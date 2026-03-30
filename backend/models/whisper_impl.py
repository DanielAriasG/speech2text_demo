import whisper
import tempfile
import os
from backend.core.asr_interface import IASRModel

class WhisperModel(IASRModel):
    def __init__(self, model_size: str = "tiny"):
        # Load model into memory/VRAM once
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_data: bytes) -> str:
        # Whisper requires a file path or a numpy array.
        # Using a temporary file for simplicity.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        try:
            result = self.model.transcribe(tmp_path)
            return result.get("text", "").strip()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
