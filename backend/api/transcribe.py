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

    # 3. Transcribe with long-form support
    try:
        transcription = transcription_service.transcribe_long_form(normalized_audio, model_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 4. Diarization
    diarization_segments = diarization_service.diarize(normalized_audio)
    formatted_diarization = [
        {"start": start, "end": end, "speaker": speaker}
        for start, end, speaker in diarization_segments
    ]

    # 5. Export results
    export_txt = export_service.export_to_txt(transcription)

    return {
        "transcription": transcription,
        "diarization": formatted_diarization,
        "exports": {
            "txt": base64.b64encode(export_txt).decode("utf-8")
        }
    }
