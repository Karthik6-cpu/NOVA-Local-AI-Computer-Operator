import json
from datetime import datetime, timezone
from nova.config import AUDIT_PATH

def log_event(event: str, details: dict) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, "details": details}
    with AUDIT_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
