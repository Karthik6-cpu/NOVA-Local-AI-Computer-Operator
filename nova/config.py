import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

APP_NAME = "NOVA"
MODEL = os.getenv("NOVA_MODEL", "qwen2.5:3b").strip()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
WORKSPACE = (PROJECT_ROOT / os.getenv("NOVA_WORKSPACE", "workspace")).resolve()
VOSK_MODEL_PATH = (PROJECT_ROOT / os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-en-us-0.15")).resolve()
AUDIT_PATH = PROJECT_ROOT / "logs" / "audit.jsonl"
