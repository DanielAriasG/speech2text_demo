import os
import tempfile
import torch
import warnings
import io
import soundfile as sf
from pyannote.audio import Pipeline

warnings.filterwarnings("ignore", category=UserWarning)
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
                token=hf_token
            )
            # Use GPU if available
            if torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda:0"))
        except Exception as e:
            print(f"Error initializing Pyannote pipeline: {e}")
            self.pipeline = None

    def diarize(self, audio_data: bytes) -> List[Tuple[float, float, str]]:
        if not self.pipeline:
            return [(0.0, 1.0, "Speaker 1")]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            with open(tmp_path, "wb") as f:
                f.write(audio_data)
                
            diarization_output = self.pipeline(tmp_path)
            
            # Handle newer Pyannote versions that return a DiarizeOutput wrapper
            if hasattr(diarization_output, "speaker_diarization"):
                annotation = diarization_output.speaker_diarization
            else:
                annotation = diarization_output
            
            segments = []
            for turn, _, speaker in annotation.itertracks(yield_label=True):
                segments.append((round(turn.start, 2), round(turn.end, 2), speaker))
                
            return segments if segments else [(0.0, 1.0, "Speaker 1")]
        except Exception as e:
            print(f"Pyannote Diarization error: {e}")
            return [(0.0, 1.0, "Speaker 1")]
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class SortformerDiarization(IDiarizationService):
    def __init__(self):
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            print("WARNING: HF_TOKEN environment variable not set. Download may fail.")
        
        try:
            from nemo.collections.asr.models import SortformerEncLabelModel
            # Load NVIDIA's streaming Sortformer model
            self.model = SortformerEncLabelModel.from_pretrained(
                "nvidia/diar_streaming_sortformer_4spk-v2.1"
            )
            
            if torch.cuda.is_available():
                self.model = self.model.to(torch.device("cuda:0"))
            self.model.eval()
        except ImportError:
            print("Error: nemo_toolkit[asr] is missing. Sortformer will not function.")
            self.model = None
        except Exception as e:
            print(f"Error initializing Sortformer pipeline: {e}")
            self.model = None

    def diarize(self, audio_data: bytes) -> List[Tuple[float, float, str]]:
        if not self.model:
            return [(0.0, 1.0, "Speaker 1")]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            with open(tmp_path, "wb") as f:
                f.write(audio_data)
                
            predicted_segments = self.model.diarize(audio=[tmp_path], batch_size=1)
            
            if isinstance(predicted_segments, list) and len(predicted_segments) > 0:
                file_segments = predicted_segments[0]
            else:
                file_segments = predicted_segments
            
            segments = []
            for seg in file_segments:
                try:
                    if isinstance(seg, str):
                        parts = seg.replace(',', ' ').split()
                        if len(parts) >= 3:
                            start = round(float(parts[0]), 2)
                            end = round(float(parts[1]), 2)
                            speaker = f"Speaker {parts[2]}" if "Speaker" not in parts[2] else parts[2]
                            segments.append((start, end, speaker))
                    elif isinstance(seg, (list, tuple)) and len(seg) >= 3:
                        start = round(float(seg[0]), 2)
                        end = round(float(seg[1]), 2)
                        speaker_label = str(seg[2])
                        speaker = f"Speaker {speaker_label}" if "Speaker" not in speaker_label else speaker_label
                        segments.append((start, end, speaker))
                    elif isinstance(seg, dict):
                        start = round(float(seg.get('start', 0.0)), 2)
                        end = round(float(seg.get('end', 0.0)), 2)
                        speaker_label = str(seg.get('speaker', '1'))
                        speaker = f"Speaker {speaker_label}" if "Speaker" not in speaker_label else speaker_label
                        segments.append((start, end, speaker))
                except (ValueError, TypeError) as e:
                    print(f"Skipping unparsable segment {seg}: {e}")
                    continue
            
            return segments if segments else [(0.0, 1.0, "Speaker 1")]
        except Exception as e:
            print(f"Sortformer Diarization error: {e}")
            return [(0.0, 1.0, "Speaker 1")]
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

class DiariZenDiarization(IDiarizationService):
    def __init__(self):
        try:
            from diarizen.pipelines.inference import DiariZenPipeline
            # Load the BUT-FIT DiariZen model
            self.pipeline = DiariZenPipeline.from_pretrained("BUT-FIT/diarizen-meeting-base")
        except ImportError:
            print("Error: diarizen package is missing. Try: pip install diarizen")
            self.pipeline = None
        except Exception as e:
            print(f"Error initializing DiariZen pipeline: {e}")
            self.pipeline = None

    def diarize(self, audio_data: bytes) -> List[Tuple[float, float, str]]:
        if not self.pipeline:
            return [(0.0, 1.0, "Speaker 1")]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        try:
            with open(tmp_path, "wb") as f:
                f.write(audio_data)
                
            diar_results = self.pipeline(tmp_path)
            
            segments = []
            for turn, _, speaker in diar_results.itertracks(yield_label=True):
                segments.append((round(turn.start, 2), round(turn.end, 2), str(speaker)))
                
            return segments if segments else [(0.0, 1.0, "Speaker 1")]
        except Exception as e:
            print(f"DiariZen Diarization error: {e}")
            return [(0.0, 1.0, "Speaker 1")]
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)