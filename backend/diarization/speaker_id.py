import os
import tempfile
import soundfile as sf
import io
import torch
from pyannote.audio import Pipeline
from backend.core.diarization_interface import IDiarizationService
from typing import List, Tuple

class PyannoteDiarization(IDiarizationService):
    def __init__(self):
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            print("WARNING: HF_TOKEN environment variable not set. Pyannote may fail.")
        
        try:
            # Load Pyannote 3.1 model. Note: user needs to accept conditions on Hugging Face.
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
            # Use GPU if available
            if torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
        except Exception as e:
            print(f"Error initializing Pyannote pipeline: {e}")
            self.pipeline = None

    def diarize(self, audio_data: bytes) -> List[Tuple[float, float, str]]:
        if not self.pipeline:
            # Fallback if pyannote failed to load
            return [(0.0, 1.0, "Speaker 1")]

        # Write audio bytes to a temporary wav file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            # Assuming audio_data is already pre-processed to 16kHz WAV format bytes
            with open(tmp_path, "wb") as f:
                f.write(audio_data)
                
            diarization = self.pipeline(tmp_path)
            
            # Format output
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                # round to 2 decimals
                start = round(turn.start, 2)
                end = round(turn.end, 2)
                segments.append((start, end, speaker))
                
            return segments
        except Exception as e:
            print(f"Diarization error: {e}")
            return [(0.0, 1.0, "Speaker 1")]
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
