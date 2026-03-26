from fastapi import APIRouter, WebSocket
import asyncio

router = APIRouter()

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive audio chunk (bytes)
            data = await websocket.receive_bytes()

            # Placeholder for streaming ASR logic
            # For now, just send back a dummy text acknowledgment
            await websocket.send_text(f"Received chunk of size {len(data)} - transcribing...")

    except Exception as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        await websocket.close()
