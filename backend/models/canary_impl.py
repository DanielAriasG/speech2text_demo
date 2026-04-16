import os
import io
import torch
import tempfile
import soundfile as sf
import librosa
from backend.core.asr_interface import IASRModel
from typing import Optional

class CanaryModel(IASRModel):
    """
    Implementation for nvidia/canary-1b using NeMo ASR.
    Supports English, Spanish, German, French.
    """
    def __init__(self, model_id: str = "nvidia/canary-1b"):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        try:
            import nemo.collections.asr as nemo_asr
            self.model = nemo_asr.models.EncDecMultiTaskModel.from_pretrained(
                model_name=model_id, 
                map_location=self.device
            )
            self.model = self.model.to(self.device)
            self.model.eval()
        except ImportError:
            print("Warning: nemo_toolkit[asr] is missing. Canary will not function.")
            self.model = None

    def transcribe(self, audio_data: bytes, language: Optional[str] = None) -> str:
        if not self.model:
            return ""
            
        audio_np, sr = sf.read(io.BytesIO(audio_data), dtype="float32")
        if len(audio_np.shape) > 1:
            audio_np = audio_np.mean(axis=1)
        if sr != 16000:
            audio_np = librosa.resample(audio_np, orig_sr=sr, target_sr=16000)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            sf.write(tmp_path, audio_np, 16000, format='WAV')
            
            # Canary requires task and source_lang tags. 
            # Default task is 'asr'. source_lang should be ISO code (en, es, de, fr).
            # If language isn't provided, it defaults to English.
            src_lang = language if language else "en"
            
            results = self.model.transcribe(
                [tmp_path], 
                task="asr", 
                source_lang=src_lang, 
                target_lang=src_lang,
                pnc="yes"
            )
            
            if results and len(results) > 0:
                return str(results[0].text).strip()
            return ""
            
        except Exception as e:
            print(f"Canary NeMo inference error: {e}")
            return ""
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)