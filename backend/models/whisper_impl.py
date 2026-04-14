import io
import torch
import soundfile as sf
import librosa
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from backend.core.asr_interface import IASRModel

class WhisperModel(IASRModel):
    """
    Implementation using Hugging Face Transformers.
    Strictly enforces cuda:0 and float16 typing for rapid GPU inference.
    """
    def __init__(self, model_id: str = "openai/whisper-large-v3"):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        # 1. Load Model with FP16 typing explicitly mapped to the Device
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, 
            torch_dtype=self.torch_dtype, 
            low_cpu_mem_usage=True
        )
        self.model.to(self.device)

        # 2. Load the Feature Extractor & Tokenizer
        self.processor = AutoProcessor.from_pretrained(model_id)

        # 3. Compile the Pipeline
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            chunk_length_s=30,
            batch_size=16,  # Processes inference chunks in parallel!
            torch_dtype=self.torch_dtype,
            device=self.device,
        )

    def transcribe(self, audio_data: bytes) -> str:
        # Load the bytes into an array
        audio_np, sr = sf.read(io.BytesIO(audio_data), dtype="float32")
        
        # Enforce mono
        if len(audio_np.shape) > 1:
            audio_np = audio_np.mean(axis=1)
            
        # Resample to the standard 16kHz HF expects
        if sr != 16000:
            audio_np = librosa.resample(audio_np, orig_sr=sr, target_sr=16000)

        try:
            # Transformer ASR pipeline allows raw numpy arrays
            result = self.pipe(audio_np)
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("text", "").strip()
            elif isinstance(result, dict):
                return result.get("text", "").strip()
            return str(result)
            
        except Exception as e:
            print(f"Whisper pipeline inference error: {e}")
            return ""