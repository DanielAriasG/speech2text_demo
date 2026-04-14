import os
import io
import sys
import torch
import tempfile
import soundfile as sf
import librosa
from backend.core.asr_interface import IASRModel

class ParakeetModel(IASRModel):
    """
    Implementation for nvidia/parakeet-tdt using NeMo ASR.
    Explicitly forces model deployment to cuda:0.
    """
    def __init__(self, model_id: str = "nvidia/parakeet-tdt-0.6b-v3"):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        # Print the device confirmation if a GPU is detected
        if self.device.startswith("cuda"):
            gpu_name = torch.cuda.get_device_name(0)
            print(f"🚀 [Parakeet] Initialized successfully on GPU: {gpu_name} ({self.device})")
        else:
            print("⚠️ [Parakeet] Initialized on CPU. Inference will be slow.")

        try:
            # --- Windows libtorchcodec Fix ---
            # If torchcodec is installed but broken (missing DLLs), 
            # mock it so torchaudio/NeMo doesn't crash during import.
            # (Note: torchaudio.set_audio_backend is deprecated and removed in >2.1)
            if os.name == 'nt':
                try:
                    import torchcodec
                except Exception:
                    sys.modules['torchcodec'] = None
            # ---------------------------------

            import nemo.collections.asr as nemo_asr
            # Parakeet uses the standard ASRModel architecture config
            self.model = nemo_asr.models.ASRModel.from_pretrained(
                model_name=model_id, 
                map_location=self.device
            )
            # Ensure it is locked onto the GPU device
            self.model = self.model.to(self.device)
            self.model.eval()
        except ImportError:
            print("Warning: nemo_toolkit[asr] is missing. Parakeet will not function.")
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
            
            # TDT/CTC models return slightly different tuple sizes, usually (texts, texts_bbox)
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
            print(f"Parakeet NeMo inference error: {e}")
            return ""
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)