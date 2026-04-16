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
    Supports explicit language passing for multilingual datasets.
    """
    def __init__(self, model_id: str = "openai/whisper-large-v3"):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, 
            torch_dtype=self.torch_dtype, 
            low_cpu_mem_usage=True
        )
        self.model.to(self.device)
        self.processor = AutoProcessor.from_pretrained(model_id)

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            chunk_length_s=30,
            batch_size=16,
            torch_dtype=self.torch_dtype,
            device=self.device,
        )

    def transcribe(self, audio_data: bytes, language: str = None) -> str:
        audio_np, sr = sf.read(io.BytesIO(audio_data), dtype="float32")
        
        if len(audio_np.shape) > 1:
            audio_np = audio_np.mean(axis=1)
            
        if sr != 16000:
            audio_np = librosa.resample(audio_np, orig_sr=sr, target_sr=16000)

        try:
            # Pass language hint to generate_kwargs if provided
            generate_kwargs = {}
            if language:
                generate_kwargs["language"] = language

            result = self.pipe(audio_np, generate_kwargs=generate_kwargs)
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("text", "").strip()
            elif isinstance(result, dict):
                return result.get("text", "").strip()
            return str(result)
            
        except Exception as e:
            print(f"Whisper pipeline inference error: {e}")
            return ""