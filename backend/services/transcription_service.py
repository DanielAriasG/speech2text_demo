import io
import soundfile as sf
from typing import List, Optional
from backend.core.model_registry import ModelRegistry

class TranscriptionService:
    def __init__(self, target_secs: int = 24, max_secs: int = 30, overlap_secs: int = 3):
        self.target_secs = target_secs
        self.max_secs = max_secs
        self.overlap_secs = overlap_secs
        # 16kHz mono 16-bit PCM = 16000 samples/sec * 2 bytes/sample = 32000 bytes/sec
        self.bytes_per_sec = 32000

    def transcribe_long_form(self, audio_data: bytes, model_name: str, language: Optional[str] = None) -> str:
        model = ModelRegistry.get_model(model_name)
        if not model:
            raise ValueError(f"Model {model_name} not found")

        total_bytes = len(audio_data)
        max_bytes = self.max_secs * self.bytes_per_sec

        if total_bytes <= max_bytes:
            return model.transcribe(audio_data, language=language).strip()

        # Load audio once to get samples
        audio_fp = io.BytesIO(audio_data)
        data, sr = sf.read(audio_fp)

        total_samples = len(data)
        chunk_samples = self.target_secs * sr
        overlap_samples = self.overlap_secs * sr

        transcriptions = []
        offset = 0

        while offset < total_samples:
            end = min(offset + chunk_samples, total_samples)
            chunk_data = data[offset:end]

            chunk_fp = io.BytesIO()
            sf.write(chunk_fp, chunk_data, sr, format='WAV')
            chunk_bytes = chunk_fp.getvalue()

            chunk_transcript = model.transcribe(chunk_bytes, language=language).strip()
            if chunk_transcript:
                transcriptions.append(chunk_transcript)

            if end == total_samples:
                break

            offset += (chunk_samples - overlap_samples)

        return " ".join(transcriptions)
