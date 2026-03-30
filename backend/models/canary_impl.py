import whisper
import tempfile
import os
from backend.core.asr_interface import IASRModel

class CanaryModel(IASRModel):
    """
    Canary model typically requires nemo_toolkit.
    Using openai/whisper-base as a high-quality functional surrogate.
    """
    def __init__(self, model_size: str = "base"):
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_data: bytes) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        try:
            result = self.model.transcribe(tmp_path)
            return result.get("text", "").strip()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
