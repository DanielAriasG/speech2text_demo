import io
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
        # Load audio from bytes
        audio_fp = io.BytesIO(audio_data)
        y, sr = librosa.load(audio_fp, sr=16000, mono=True)

        # Save processed audio to bytes
        output_fp = io.BytesIO()
        sf.write(output_fp, y, 16000, format='WAV')
        return output_fp.getvalue()
