from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.services.audio_service import AudioService
from backend.services.transcription_service import TranscriptionService
from backend.diarization.speaker_id import PyannoteDiarization, SortformerDiarization
from backend.services.export_service import ExportService
import base64

router = APIRouter()
audio_service = AudioService()
transcription_service = TranscriptionService()
export_service = ExportService()

@router.post("/transcribe")
async def transcribe_audio(
    model_name: str = Form("whisper"),
    diarization_model: str = Form("pyannote"),
    file: UploadFile = File(...)
):
    # 1. Read file
    audio_data = await file.read()

    # 2. Preprocess audio
    normalized_audio = audio_service.preprocess(audio_data)

    # 3. Select Diarization Service
    if diarization_model == "sortformer":
        diar_service = SortformerDiarization()
    else:
        diar_service = PyannoteDiarization()

    # 4. Perform Diarization
    diarization_segments = diar_service.diarize(normalized_audio)
    raw_segments = [
        {"start": start, "end": end, "speaker": speaker}
        for start, end, speaker in diarization_segments
    ]

    # 5. Transcribe with Diarization
    try:
        final_segments = transcription_service.transcribe_with_diarization(
            normalized_audio, model_name, raw_segments, audio_service
        )
        full_transcription = " ".join([s["text"] for s in final_segments])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 6. Export results
    export_txt = export_service.export_to_txt(full_transcription, final_segments)

    return {
        "transcription": full_transcription,
        "diarization": final_segments,
        "exports": {
            "txt": base64.b64encode(export_txt).decode("utf-8")
        }
    }
