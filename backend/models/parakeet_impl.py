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
        import io
        import soundfile as sf
        import numpy as np
        
        audio_np, sr = sf.read(io.BytesIO(audio_data), dtype="float32")
        
        if len(audio_np.shape) > 1:
            audio_np = audio_np.mean(axis=1)
            
        if sr != 16000:
            import librosa
            audio_np = librosa.resample(audio_np, orig_sr=sr, target_sr=16000)

        try:
            # Transformers ASR pipeline allows raw numpy arrays
            result = self.pipe(audio_np)
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("text", "").strip()
            elif isinstance(result, dict):
                return result.get("text", "").strip()
            return str(result)
        except Exception as e:
            print(f"Parakeet inference error: {e}")
            return ""
