import audioop
import asyncio
import base64
import json

from twilio.rest import Client
from fastapi import WebSocketDisconnect
from google.genai import types

from app.interview import InterviewState
from app.storage import save_call_result

from app.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN
)

def end_call(call_sid: str):
    try:
        client = Client(
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN
        )

        client.calls(call_sid).update(
            status="completed"
        )

        print(f"Call {call_sid} terminated")

    except Exception as e:
        print(f"Failed to terminate call: {e}")

async def generate_hindi_summary(client, responses) -> str:
    qa_text = ""
    for r in responses:
        qa_text += f"प्रश्न: {r['question']}\nउत्तर: {r['answer']}\n\n"
    
    prompt = f"""
मरीज के साक्षात्कार का विवरण नीचे दिया गया है:
{qa_text}
ऊपर दिए गए प्रश्न और उत्तर के आधार पर मरीज की स्थिति का एक संक्षिप्त और स्पष्ट सारांश हिंदी में एक पैराग्राफ में लिखें।
उदाहरण के लिए:
प्रश्न: आज आपको सबसे ज़्यादा किस बात की तकलीफ़ है? | उत्तर: बुखार और चक्कर आ रहे हैं।
प्रश्न: यह तकलीफ़ कब से है? | उत्तर: तीन दिन से।
प्रश्न: अभी यह तकलीफ़ कितनी ज़्यादा है? | उत्तर: 10 में से 8 के स्तर पर है।
प्रश्न: समय के साथ यह तकलीफ़ कैसी हुई है? | उत्तर: समय के साथ बुखार बढ़ता जा रहा है।
प्रश्न: क्या आपने इसके लिए कोई इलाज या दवा ली है? | उत्तर: नहीं ली है।
सारांश: मरीज पिछले 3 दिनों से बुखार और चक्कर की शिकायत कर रहा/रही है। तकलीफ़ की गंभीरता 10 में से 8 है तथा समय के साथ बुखार बढ़ रहा है। मरीज ने अभी तक कोई दवा या उपचार शुरू नहीं किया है।

कृपया केवल सारांश पैराग्राफ ही वापस करें। कोई अन्य पाठ, लेबल या अतिरिक्त स्पष्टीकरण न जोड़ें।
"""
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "साक्षात्कार पूरा हो गया है।"

async def bridge_call(
        websocket,
        gemini_session,
        state,
        stream_sid,
        gemini_client
):

    inbound_state = None
    outbound_state = None

    async def twilio_to_gemini():
        nonlocal inbound_state
        while True:
            try:
                data = await websocket.receive_text()
                msg = json.loads(data)
                event = msg.get("event")

                if event == "media":
                    media = msg.get("media")
                    if media:
                        # Decode the mu-law audio payload (base64)
                        payload = base64.b64decode(media["payload"])
                        # Convert 8kHz mu-law to 16-bit linear PCM (8kHz)
                        pcm_8k = audioop.ulaw2lin(payload, 2)
                        # Resample 8kHz linear PCM to 16kHz linear PCM
                        pcm_16k, inbound_state = audioop.ratecv(
                            pcm_8k, 2, 1, 8000, 16000, inbound_state
                        )
                        # Send 16kHz linear PCM to Gemini
                        await gemini_session.send_realtime_input(
                            audio=types.Blob(
                                data=pcm_16k,
                                mime_type="audio/pcm;rate=16000"
                            )
                        )
                elif event == "stop":
                    break
            except Exception as e:
                print(f"Error in twilio_to_gemini: {e}")
                break

    async def gemini_to_twilio():
        nonlocal outbound_state
        while True:
            try:
                async for response in gemini_session.receive():
                    # Check if the model has finished saying goodbye, and if so, terminate
                    if response.server_content and response.server_content.turn_complete:
                        if getattr(state, "goodbye_sent", False):
                            # Give Twilio 5 seconds to finish playing the audio
                            await asyncio.sleep(5)
                            end_call(state.call_sid)
                            return

                    if response.tool_call:
                        for fc in response.tool_call.function_calls:
                            if fc.name == "submit_answer":
                                answer = fc.args["answer"]
                                state.save_answer(answer)
                                await gemini_session.send_tool_response(
                                    function_responses=[
                                        types.FunctionResponse(
                                            name="submit_answer",
                                            id=fc.id,
                                            response={
                                                "status": "saved"
                                            }
                                        )
                                    ]
                                )

                                print("state is :- ", state.completed())

                                if state.completed():
                                    summary_text = await generate_hindi_summary(gemini_client, state.responses)
                                    result = {
                                        "call_sid": state.call_sid,
                                        "completed": True,
                                        "summary": summary_text
                                    }
                                    save_call_result(state.call_sid, result)
                                    print(f"\n--- INTERVIEW COMPLETED FOR CALL: {state.call_sid} ---")
                                    print(json.dumps(result, indent=2))
                                    print("--------------------------------------------------\n")

                                    await gemini_session.send_client_content(
                                        turns=types.Content(
                                            role="user",
                                            parts=[
                                                types.Part(
                                                    text="The interview is now complete. Tell the user exactly: 'आपके सहयोग के लिए धन्यवाद। आपका दिन शुभ हो।' and then stop speaking. Do not say anything else."
                                                )
                                            ]
                                        ),
                                        turn_complete=True
                                    )
                                    state.goodbye_sent = True
                                    continue

                                next_question = state.current_question_text()
                                await gemini_session.send_client_content(
                                    turns=types.Content(
                                        role="user",
                                        parts=[
                                            types.Part(
                                                text=f"Ask: {next_question}"
                                            )
                                        ]
                                    ),
                                    turn_complete=True
                                )

                    if (
                        response.server_content
                        and
                        response.server_content.model_turn
                    ):
                        for part in response.server_content.model_turn.parts:
                            if not part.inline_data:
                                continue

                            # Gemini sends 24kHz 16-bit linear PCM
                            pcm_24k = part.inline_data.data
                            # Resample 24kHz linear PCM to 8kHz linear PCM
                            pcm_8k, outbound_state = audioop.ratecv(
                                pcm_24k, 2, 1, 24000, 8000, outbound_state
                            )
                            # Convert 8kHz linear PCM to 8-bit mu-law (8kHz)
                            ulaw_data = audioop.lin2ulaw(pcm_8k, 2)
                            payload = base64.b64encode(ulaw_data).decode()

                            await websocket.send_json(
                                {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {
                                        "payload": payload
                                    }
                                }
                            )
            except Exception as e:
                print(f"Error in gemini_to_twilio: {e}")
                break

    try:
        await asyncio.gather(
            twilio_to_gemini(),
            gemini_to_twilio()
        )
    except WebSocketDisconnect:
        print(f"Twilio call {state.call_sid} disconnected.")
    except Exception as e:
        print(f"Error in call bridge {state.call_sid}: {e}")