"""Motor de test: reda starea dintr-un fisier JSON, recitit des, ca sa poti
schimba scenariul cu aplicatia pornita. Nu trimite nimic pe net (raportul de
bug raspunde fals). Pornit de main.js cand exista ARAM_MOCK=<fisier>.

    python mock_engine.py <scenariu.json>
"""

import json
import pathlib
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
path = pathlib.Path(sys.argv[1])
lock = threading.Lock()


def emit(msg):
    with lock:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()


def replay():
    last = None
    while True:
        try:
            text = path.read_text(encoding="utf-8")
            if text != last:
                last = text
                emit(dict(json.loads(text), t="state"))
        except (OSError, ValueError):
            pass
        time.sleep(0.3)


emit(
    {
        "t": "hello",
        "version": "test",
        "icons": str(ROOT / "ingame-app" / "data" / "icons"),
        "counts": {"champions": 173, "augments": 535, "builds": 173},
    }
)
threading.Thread(target=replay, daemon=True).start()
for raw in sys.stdin:
    msg = json.loads(raw)
    if msg.get("cmd") == "quit":
        break
    if msg.get("cmd") == "diag":
        emit({"t": "reply", "id": msg["id"], "text": "version: test\nwindows: test\nphase: test"})
    elif msg.get("cmd") == "report":
        emit(
            {
                "t": "reply",
                "id": msg["id"],
                "ok": False,
                "text": "Test mode: the report is not sent.",
            }
        )
    print(json.dumps(msg), file=sys.stderr, flush=True)
