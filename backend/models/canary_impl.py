import os
import io
import torch
import tempfile
import soundfile as sf
import librosa
from backend.core.asr_interface import IASRModel

class CanaryModel(IASRModel):
    """
    Implementation for nvidia/canary-1b using NeMo ASR.
    Explicitly forces model deployment to cuda:0.
    """
    def __init__(self, model_id: str = "nvidia/canary-1b"):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        try:
            import nemo.collections.asr as nemo_asr
            # Canary specifically utilizes the EncDecMultiTaskModel backbone in NeMo
            self.model = nemo_asr.models.EncDecMultiTaskModel.from_pretrained(
                model_name=model_id, 
                map_location=self.device
            )
            # Ensure it is locked onto the GPU device
            self.model = self.model.to(self.device)
            self.model.eval()
        except ImportError:
            print("Warning: nemo_toolkit[asr] is missing. Canary will not function.")
            self.model = None

    def transcribe(self, audio_data: bytes) -> str:
        if not self.model:
            return ""
            
        audio_np, sr = sf.read(io.BytesIO(audio_data), dtype="float32")
        
        if len(audio_np.shape) > 1:
            audio_np = audio_np.mean(axis=1)
            
        if sr != 16000:
            audio_np = librosa.resample(audio_np, orig_sr=sr, target_sr=16000)

        # NeMo models heavily rely on path inference. Write the normalized chunk to a temp file.
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            sf.write(tmp_path, audio_np, 16000, format='WAV')
            
            # NeMo batch transcribe
            results = self.model.transcribe([tmp_path])
            
            if isinstance(results, tuple) and len(results) > 0:
                text = results[0][0]
            elif isinstance(results, list) and len(results) > 0:
                if isinstance(results[0], list):
                    text = results[0][0]
                else:
                    text = results[0].text
            else:
                text = ""
                
            return str(text).strip()
            
        except Exception as e:
            print(f"Canary NeMo inference error: {e}")
            return ""
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)