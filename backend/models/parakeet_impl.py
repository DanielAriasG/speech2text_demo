import torch
from transformers import pipeline
from backend.core.asr_interface import IASRModel

class ParakeetModel(IASRModel):
    def __init__(self, model_id: str = "nvidia/parakeet-ctc-0.6b"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model_id,
            device=device
        )

    def transcribe(self, audio_data: bytes) -> str:
        # The pipeline can handle raw bytes if they are in a supported format
        # but often it's safer to provide a numpy array or a file.
        # We'll use a temporary file for consistency with Whisper.
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        try:
            result = self.pipe(tmp_path)
            return result.get("text", "").strip()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
