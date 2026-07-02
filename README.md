# Gemini + Twilio Voice Conversation

A simple FastAPI application that connects Twilio voice calls to Google Gemini Live for an automated medical interview.

## What this app does

- Starts a phone call through Twilio.
- Twilio sends the live audio stream to the FastAPI app using WebSockets.
- The app forwards caller audio to Gemini and receives Gemini audio responses.
- Gemini asks a series of medical questions and submits the caller's answers back to the app.
- Completed interview results are saved as JSON files in `data/call_results`.

## Main components

### `run.py`
- Starts the FastAPI server with Uvicorn.
- Uses `app.main:app` as the entry point.

### `app/main.py`
- Defines the HTTP and WebSocket API.
- Endpoints:
  - `POST /trigger-call` and `GET /trigger-call`: trigger a Twilio call to a phone number.
  - `GET /call-results/{call_sid}`: fetch result JSON for a completed call.
  - `GET /call-results`: list all saved call results.
  - `POST /incoming-call`: Twilio webhook returns XML that routes the call into the media stream.
  - `WebSocket /media-stream`: receives Twilio media events and bridges audio to Gemini.

### `app/config.py`
- Loads environment variables from `.env`.
- Contains API keys and Twilio configuration values used by the app.

### `app/gemini_client.py`
- Wraps the Gemini Live API client.
- Builds a live config with instructions for conducting a structured interview.
- Declares a tool called `submit_answer` that Gemini can call to save answers.

### `app/interview.py`
- Manages simple interview state.
- Keeps track of the current question and saved responses.
- Contains the predefined list of questions.

### `app/twilio_stream.py`
- Bridges Twilio audio and Gemini audio.
- Converts Twilio's 8kHz mu-law audio into Gemini-compatible PCM audio.
- Converts Gemini's 24kHz PCM output back to Twilio's 8kHz mu-law audio.
- Handles Gemini tool calls to save interview answers.

### `app/storage.py`
- Saves completed interview results to `data/call_results/<call_sid>.json`.
- Ensures the result directory exists.

## How the voice call works

1. User triggers the call through the `/trigger-call` endpoint.
2. Twilio makes the call and requests `/incoming-call`.
3. The app returns TwiML that connects the call to `/media-stream`.
4. Twilio sends audio events to the WebSocket endpoint.
5. The app forwards caller audio to Gemini and receives Gemini speech responses.
6. Gemini uses the `submit_answer` tool to send extracted answers back to the app.
7. When the interview is finished, the app saves the full result to `data/call_results`.

## Environment variables

The app expects these values in a `.env` file or environment:

- `GEMINI_API_KEY`
- `PUBLIC_URL`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_NUMBER`

## Running the app

1. Install dependencies from `requirements.txt`.
2. Set environment variables.
3. Start the app with:

```bash
python run.py
```

4. Use `/trigger-call` to place a call.

## Files to know

- `run.py`: server launcher.
- `app/main.py`: HTTP and WebSocket API.
- `app/gemini_client.py`: Gemini Live config and tool definition.
- `app/twilio_stream.py`: audio bridge and interview coordination.
- `app/interview.py`: interview question flow.
- `app/storage.py`: result persistence.

## Notes

- The current interview contains 4 questions.
- Results are stored locally in `data/call_results`.
- The app is designed for voice interaction and uses audio conversion to bridge Twilio and Gemini.
