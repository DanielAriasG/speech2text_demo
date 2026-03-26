from backend.core.asr_interface import IASRModel

class ParakeetModel(IASRModel):
    def transcribe(self, audio_data: bytes) -> str:
        # Placeholder for actual Parakeet logic
        return "[Parakeet Transcription Placeholder]"
