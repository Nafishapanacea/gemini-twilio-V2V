import json
import asyncio
from pathlib import Path
from typing import Dict


RESULT_DIR = Path("data/call_results")

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# In-memory registry to track active calls.
active_calls: Dict[str, asyncio.Event] = {}


def register_call(call_sid: str):
    if call_sid not in active_calls:
        active_calls[call_sid] = asyncio.Event()


def signal_call_finished(call_sid: str):
    event = active_calls.get(call_sid)
    if event:
        event.set()


def unregister_call(call_sid: str):
    active_calls.pop(call_sid, None)


def save_call_result(call_sid, result):

    file = RESULT_DIR / f"{call_sid}.json"

    with open(file, "w", encoding="utf-8") as f:

        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False
        )