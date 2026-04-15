import os
import io
import torch
import tempfile
import soundfile as sf
import librosa
from backend.core.asr_interface import IASRModel

class CanaryModel(IASRModel):
    """
    Implementation for nvidia/canary-1b-v2 using NeMo ASR.
    Supports dynamic source and target language selection.
    """
    def __init__(self, model_id: str = "nvidia/canary-1b-v2"):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        try:
            import nemo.collections.asr as nemo_asr
            self.model = nemo_asr.models.EncDecMultiTaskModel.from_pretrained(
                model_name=model_id, 
                map_location=self.device
            )
            self.model = self.model.to(self.device)
            self.model.eval()
            print(f"🚀 [Canary V2] Loaded successfully on {self.device}")
        except ImportError:
            print("Warning: nemo_toolkit[asr] is missing. Canary will not function.")
            self.model = None

    def transcribe(self, audio_data: bytes, language: str = "en") -> str:
        """
        Transcribes audio with specific language code (e.g., 'es', 'pl', 'en').
        """
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
            
            # Use the provided language for both source and target (transcription)
            results = self.model.transcribe(
                [tmp_path], 
                source_lang=language, 
                target_lang=language
            )
            
            if isinstance(results, list) and len(results) > 0:
                first_res = results[0]
                return (first_res.text if hasattr(first_res, 'text') else str(first_res)).strip()
            return ""
            
        except Exception as e:
            print(f"Canary V2 NeMo inference error: {e}")
            return ""
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)