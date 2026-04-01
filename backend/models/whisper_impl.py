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
        import io
        import soundfile as sf
        import numpy as np
        
        # Whisper expects 16000Hz audio as a 1D float32 numpy array
        audio_np, sr = sf.read(io.BytesIO(audio_data), dtype="float32")
        
        # Convert to mono if it's stereo
        if len(audio_np.shape) > 1:
            audio_np = audio_np.mean(axis=1)
            
        # Resample to 16000Hz (Whisper's mandatory sample rate) if necessary
        if sr != 16000:
            import librosa
            audio_np = librosa.resample(audio_np, orig_sr=sr, target_sr=16000)

        try:
            # CPU doesn't support fp16 in many versions of whisper
            fp16 = torch.cuda.is_available()
            
            # OpenAI Whisper natively supports numpy array input directly!
            result = self.model.transcribe(audio_np, fp16=fp16)
            return result.get("text", "").strip()
        except Exception as e:
            print(f"Whisper inference error: {e}")
            return ""
