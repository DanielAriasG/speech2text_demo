from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.transcription_service import TranscriptionService
from backend.services.audio_service import AudioService

router = APIRouter()
audio_service = AudioService()
transcription_service = TranscriptionService()

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # We expect the frontend to send aggregated audio chunks that form a complete readable file (e.g. growing WAV/Webm blob)
    try:
        while True:
            data = await websocket.receive_bytes()
            
            try:
                processed_bytes = audio_service.preprocess(data)
                text = transcription_service.transcribe_long_form(processed_bytes, "whisper")
                await websocket.send_text(text)
            except Exception as e:
                # If preprocessing fails (e.g., partial chunk that librosa can't read), ignore or notify
                pass

    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket connection closed with error: {e}")
