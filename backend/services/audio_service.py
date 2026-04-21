import io
import os
import tempfile
import librosa
import soundfile as sf
from backend.core.audio_interface import IAudioService

# Pre-resolve librosa's lazy modules to prevent inspect.stack() crashes 
# with speechbrain's k2_fsa integration during audio processing.
import librosa.core.audio as L
_ = getattr(L, 'samplerate', None)
_ = getattr(L, 'resampy', None)
_ = getattr(L, 'soxr', None)
_ = getattr(L, 'soundfile', None)

class AudioService(IAudioService):
    def preprocess(self, audio_data: bytes) -> bytes:
        """
        Normalize audio to 16kHz mono.
        """
        # Write to temp file to support WebM/Ogg browser blobs natively via ffmpeg
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            # Load audio from physical temp path instead of BytesIO
            y, sr = librosa.load(tmp_path, sr=16000, mono=True)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Save processed audio to bytes
        output_fp = io.BytesIO()
        sf.write(output_fp, y, 16000, format='WAV')
        return output_fp.getvalue()