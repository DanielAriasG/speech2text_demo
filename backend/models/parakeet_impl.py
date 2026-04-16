import os
import io
import sys
import torch
import tempfile
import soundfile as sf
import librosa
from backend.core.asr_interface import IASRModel
from typing import Optional

class ParakeetModel(IASRModel):
    """
    Implementation for nvidia/parakeet-tdt using NeMo ASR.
    Multilingual version supports 25+ languages automatically or via manifest.
    """
    def __init__(self, model_id: str = "nvidia/parakeet-tdt-0.6b-v3"):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        try:
            import nemo.collections.asr as nemo_asr
            self.model = nemo_asr.models.ASRModel.from_pretrained(
                model_name=model_id, 
                map_location=self.device
            )
            self.model = self.model.to(self.device)
            self.model.eval()
        except ImportError:
            print("Warning: nemo_toolkit[asr] is missing. Parakeet will not function.")
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
            
            # Parakeet v3 often handles language ID internally, 
            # but we can pass language hints if the interface allows.
            results = self.model.transcribe([tmp_path])
            
            if isinstance(results, tuple) and len(results) > 0:
                text = results[0][0]
            elif isinstance(results, list) and len(results) > 0:
                if hasattr(results[0], 'text'):
                    text = results[0].text
                else:
                    text = results[0][0]
            else:
                text = ""
                
            return str(text).strip()
            
        except Exception as e:
            print(f"Parakeet NeMo inference error: {e}")
            return ""
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)