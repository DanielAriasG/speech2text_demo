import io
import soundfile as sf
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.services.audio_service import AudioService
from backend.services.transcription_service import TranscriptionService
from backend.diarization.speaker_id import PyannoteDiarization
from backend.services.export_service import ExportService
import base64

router = APIRouter()
audio_service = AudioService()
transcription_service = TranscriptionService()
diarization_service = PyannoteDiarization()
export_service = ExportService()

@router.post("/transcribe")
async def transcribe_audio(
    model_name: str = Form("whisper"),
    file: UploadFile = File(...)
):
    # 1. Read file
    audio_data = await file.read()

    # 2. Preprocess audio
    normalized_audio = audio_service.preprocess(audio_data)

    # 3. Diarization First
    diarization_segments = diarization_service.diarize(normalized_audio)
    
    formatted_diarization = []
    transcription_parts = []
    
    try:
        if not diarization_segments or (len(diarization_segments) == 1 and diarization_segments[0][0] == 0.0 and diarization_segments[0][1] == 1.0):
            # Fallback if no diarization (e.g. pyannote failed) or dummy segment returned
            full_text = transcription_service.transcribe_long_form(normalized_audio, model_name)
            if full_text.strip():
                formatted_diarization.append({
                    "start": 0.0,
                    "end": 0.0,
                    "speaker": "Speaker 1",
                    "text": full_text.strip()
                })
                transcription_parts.append(full_text.strip())
        else:
            # Slicing audio by diarization segments
            data, sr = sf.read(io.BytesIO(normalized_audio))
            for start_time, end_time, speaker in diarization_segments:
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                
                segment_data = data[start_sample:end_sample]
                if len(segment_data) == 0:
                    continue
                    
                chunk_fp = io.BytesIO()
                sf.write(chunk_fp, segment_data, sr, format='WAV')
                chunk_bytes = chunk_fp.getvalue()
                
                segment_text = transcription_service.transcribe_long_form(chunk_bytes, model_name)
                
                if segment_text and segment_text.strip():
                    formatted_diarization.append({
                        "start": start_time,
                        "end": end_time,
                        "speaker": speaker,
                        "text": segment_text.strip()
                    })
                    transcription_parts.append(segment_text.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    full_transcription = " ".join(transcription_parts)

    # 5. Export results
    export_txt = export_service.export_to_txt(full_transcription)
    export_docx = export_service.export_to_docx(full_transcription)
    export_pdf = export_service.export_to_pdf(full_transcription)

    return {
        "transcription": full_transcription,
        "diarization": formatted_diarization,
        "exports": {
            "txt": base64.b64encode(export_txt).decode("utf-8"),
            "docx": base64.b64encode(export_docx).decode("utf-8"),
            "pdf": base64.b64encode(export_pdf).decode("utf-8")
        }
    }
