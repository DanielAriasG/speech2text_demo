from backend.core.asr_interface import IASRModel

class WhisperModel(IASRModel):
    def transcribe(self, audio_data: bytes) -> str:
        # Placeholder for actual Whisper-large-v3 logic
        return "[Whisper Transcription Placeholder]"
