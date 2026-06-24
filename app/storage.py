import json
from pathlib import Path


RESULT_DIR = Path("data/call_results")

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def save_call_result(call_sid, result):

    file = RESULT_DIR / f"{call_sid}.json"

    with open(file, "w", encoding="utf-8") as f:

        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False
        )