import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from twilio.rest import Client
from google.genai import types
from fastapi.middleware.cors import CORSMiddleware

from app.config import *
from app.gemini_client import GeminiInterview
from app.interview import InterviewState
from app.twilio_stream import bridge_call
from app.storage import RESULT_DIR, active_calls, register_call

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TriggerCallRequest(BaseModel):
    phone_number: str

@app.post("/trigger-call")
async def trigger_call(request: TriggerCallRequest):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_NUMBER:
        raise HTTPException(
            status_code=500,
            detail="Twilio configuration is missing from environment variables."
        )
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=request.phone_number,
            from_=TWILIO_NUMBER,
            url=f"{PUBLIC_URL}/incoming-call"
        )
        register_call(call.sid)
        return {
            "status": "success",
            "message": f"Call initiated successfully to {request.phone_number}",
            "call_sid": call.sid
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate call: {str(e)}"
        )

# For production
@app.get("/trigger-call")
async def trigger_call_get(phone_number: str):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_NUMBER:
        raise HTTPException(
            status_code=500,
            detail="Twilio configuration is missing from environment variables."
        )
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        call = client.calls.create(
            to=phone_number,
            from_=TWILIO_NUMBER,
            url=f"{PUBLIC_URL}/incoming-call"
        )
        register_call(call.sid)
        return {
            "status": "success",
            "message": f"Call initiated successfully to {phone_number}",
            "call_sid": call.sid
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate call: {str(e)}"
        )

@app.get("/call-results/{call_sid}")
async def get_call_results(call_sid: str, wait: bool = False):
    file_path = RESULT_DIR / f"{call_sid}.json"
    
    if wait and not file_path.exists():
        # Check if the call is currently active
        event = active_calls.get(call_sid)
        if event:
            try:
                # Wait for the call to end (up to 5 minutes)
                await asyncio.wait_for(event.wait(), timeout=300.0)
            except asyncio.TimeoutError:
                pass
        else:
            # If the call is not active, wait briefly to see if it starts up or is written
            timeout = 10.0
            interval = 0.5
            elapsed = 0.0
            while elapsed < timeout and not file_path.exists():
                event = active_calls.get(call_sid)
                if event:
                    try:
                        await asyncio.wait_for(event.wait(), timeout=(timeout - elapsed))
                    except asyncio.TimeoutError:
                        pass
                    break
                await asyncio.sleep(interval)
                elapsed += interval

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Call results not found."
        )
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading call results: {str(e)}"
        )

@app.get("/call-results")
async def list_call_results():
    try:
        results = []
        for file_path in RESULT_DIR.glob("*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                results.append(json.load(f))
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing call results: {str(e)}"
        )

@app.post("/incoming-call")
async def incoming_call():
    # Convert HTTP(S) url to WS(S) protocol for Twilio stream
    stream_url = PUBLIC_URL.replace("https://", "wss://").replace("http://", "ws://")
    xml = f"""
        <Response>
        <Connect>
        <Stream url="{stream_url}/media-stream"/>
        </Connect>
        </Response>
    """

    return Response(
        xml,
        media_type="application/xml"
    )

@app.websocket("/media-stream")
async def media_stream(
    websocket: WebSocket
):

    await websocket.accept()

    # Wait for the start event from Twilio (connected event may come first)
    stream_sid = None
    call_sid = "demo-call"
    try:
        try:
            while True:
                message = await websocket.receive_text()
                event_data = json.loads(message)
                event = event_data.get("event")
                if event == "connected":
                    continue
                elif event == "start":
                    stream_sid = event_data["start"]["streamSid"]
                    call_sid = event_data["start"].get("callSid", call_sid)
                    register_call(call_sid)
                    break
                else:
                    print(f"Warning: Expected start/connected event, got: {event}")
                    break
        except Exception as e:
            print(f"Error receiving start event from Twilio: {e}")
            await websocket.close()
            return

        state = InterviewState(
            call_sid=call_sid
        )

        gemini = GeminiInterview(
            GEMINI_API_KEY
        )

        config = gemini.build_config()

        async with gemini.client.aio.live.connect(
            model=gemini.model,
            config=config
        ) as session:

            await session.send_client_content(
                turns=types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            text=f"""
                                Ask exactly:

                                {state.current_question_text()}
                            """
                        )
                    ]
                ),
                turn_complete=True
            )

            await bridge_call(
                websocket,
                session,
                state,
                stream_sid,
                gemini.client
            )
    finally:
        if call_sid != "demo-call":
            from app.storage import signal_call_finished, unregister_call
            signal_call_finished(call_sid)
            # Give pending long polls a short window to fetch and return results before unregistering
            await asyncio.sleep(5)
            unregister_call(call_sid)