import io
import json
import asyncio
import base64
import soundfile as sf
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.services.transcription_service import TranscriptionService
from backend.services.audio_service import AudioService
from backend.services.export_service import ExportService
from backend.api.transcribe import diarization_registry
from typing import Optional

router = APIRouter()
audio_service = AudioService()
transcription_service = TranscriptionService()
export_service = ExportService()

@router.websocket("/stream")
async def websocket_endpoint(
    websocket: WebSocket,
    model: str = Query("whisper"),
    diarization: str = Query("sortformer"),
    language: Optional[str] = Query(None)
):
    await websocket.accept()
    
    # Safely retrieve the targeted diarizer from the global memory registry
    diarizer = diarization_registry.get(diarization, diarization_registry["sortformer"])
    
    try:
        while True:
            # Await incoming audio bytes from the client continuously
            data = await websocket.receive_bytes()
            
            # Define the heavy CPU/GPU workload logic as a blocking function
            def process_audio_chunk(audio_bytes):
                try:
                    processed_bytes = audio_service.preprocess(audio_bytes)
                    diarization_segments = diarizer.diarize(processed_bytes)
                    
                    formatted_diarization = []
                    transcription_parts = []
                    
                    # Fallback condition if diarization outputs a single block or fails
                    if not diarization_segments or (len(diarization_segments) == 1 and diarization_segments[0][0] == 0.0 and diarization_segments[0][1] == 1.0):
                        full_text = transcription_service.transcribe_long_form(processed_bytes, model, language=language)
                        if full_text and full_text.strip():
                            formatted_diarization.append({
                                "start": 0.0,
                                "end": 0.0,
                                "speaker": "Speaker 1",
                                "text": full_text.strip()
                            })
                            transcription_parts.append(full_text.strip())
                    else:
                        # Slice the audio chunks based on Diarization segments
                        data_np, sr = sf.read(io.BytesIO(processed_bytes))
                        for start_time, end_time, speaker in diarization_segments:
                            start_sample = int(start_time * sr)
                            end_sample = int(end_time * sr)
                            
                            segment_data = data_np[start_sample:end_sample]
                            if len(segment_data) == 0:
                                continue
                                
                            chunk_fp = io.BytesIO()
                            sf.write(chunk_fp, segment_data, sr, format='WAV')
                            chunk_bytes = chunk_fp.getvalue()
                            
                            segment_text = transcription_service.transcribe_long_form(chunk_bytes, model, language=language)
                            
                            if segment_text and segment_text.strip():
                                formatted_diarization.append({
                                    "start": start_time,
                                    "end": end_time,
                                    "speaker": speaker,
                                    "text": segment_text.strip()
                                })
                                transcription_parts.append(segment_text.strip())
                                
                    # Generate live exports based on the current state of transcription
                    # Note: We pass the formatted_diarization to generate consistent multi-format files
                    export_txt = export_service.export_to_txt(formatted_diarization)
                    export_docx = export_service.export_to_docx(formatted_diarization)
                    export_pdf = export_service.export_to_pdf(formatted_diarization)

                    return {
                        "transcription": " ".join(transcription_parts),
                        "diarization": formatted_diarization,
                        "exports": {
                            "txt": base64.b64encode(export_txt).decode("utf-8"),
                            "docx": base64.b64encode(export_docx).decode("utf-8"),
                            "pdf": base64.b64encode(export_pdf).decode("utf-8")
                        }
                    }
                except Exception as e:
                    print(f"Error during stream processing: {e}")
                    return None

            # Execute the heavy workload in a separate asynchronous thread pool.
            result = await asyncio.to_thread(process_audio_chunk, data)
            
            # Send the structured JSON response back to the React UI
            if result:
                await websocket.send_text(json.dumps(result))

    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket connection closed with error: {e}")