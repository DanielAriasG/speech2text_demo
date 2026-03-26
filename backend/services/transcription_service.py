from typing import List
from backend.core.model_registry import ModelRegistry

class TranscriptionService:
    def __init__(self, target_secs: int = 24, max_secs: int = 30, overlap_secs: int = 3):
        self.target_secs = target_secs
        self.max_secs = max_secs
        self.overlap_secs = overlap_secs
        # Assuming 16kHz mono 16-bit PCM for byte calculations
        self.bytes_per_sec = 32000

    def transcribe_long_form(self, audio_data: bytes, model_name: str) -> str:
        model = ModelRegistry.get_model(model_name)
        if not model:
            raise ValueError(f"Model {model_name} not found")

        total_bytes = len(audio_data)
        max_bytes = self.max_secs * self.bytes_per_sec

        if total_bytes <= max_bytes:
            return model.transcribe(audio_data)

        chunk_size = self.target_secs * self.bytes_per_sec
        overlap_size = self.overlap_secs * self.bytes_per_sec

        transcriptions = []
        offset = 0

        while offset < total_bytes:
            end = min(offset + chunk_size, total_bytes)
            chunk = audio_data[offset:end]

            chunk_transcript = model.transcribe(chunk)
            # Remove placeholder brackets if present for cleaner stitching in this demo
            clean_transcript = chunk_transcript.replace("[", "").replace("]", "")
            transcriptions.append(clean_transcript)

            if end == total_bytes:
                break

            offset += (chunk_size - overlap_size)

        return " ".join(transcriptions)
