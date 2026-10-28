import json
import queue
import re
import threading
import time

from nova.config import VOSK_MODEL_PATH

def _load_voice_dependencies():
    try:
        import sounddevice as sd
        from vosk import Model, KaldiRecognizer
    except ImportError as exc:
        raise RuntimeError(
            "Offline voice packages are missing. Run: python -m pip install -r requirements-voice.txt"
        ) from exc
    if not VOSK_MODEL_PATH.exists():
        raise RuntimeError(
            f"Vosk model folder not found: {VOSK_MODEL_PATH}\n"
            "Download a small English model from https://alphacephei.com/vosk/models, "
            "extract it under models/, then set VOSK_MODEL_PATH in .env if needed."
        )
    return sd, Model, KaldiRecognizer

def listen_once() -> str:
    sd, Model, KaldiRecognizer = _load_voice_dependencies()
    audio_queue = queue.Queue()
    try:
        model = Model(str(VOSK_MODEL_PATH))
        recognizer = KaldiRecognizer(model, 16000)

        def callback(indata, frames, time_info, status):
            audio_queue.put(bytes(indata))

        chunks = []
        with sd.RawInputStream(
            samplerate=16000, blocksize=8000, dtype="int16",
            channels=1, callback=callback
        ):
            started = time.time()
            last_speech = started
            heard = False
            while time.time() - started < 12:
                try:
                    data = audio_queue.get(timeout=1)
                except queue.Empty:
                    continue
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    phrase = result.get("text", "").strip()
                    if phrase:
                        chunks.append(phrase)
                        break
                else:
                    partial = json.loads(recognizer.PartialResult()).get("partial", "")
                    if partial:
                        heard = True
                        last_speech = time.time()
                if heard and time.time() - last_speech > 2.5:
                    break
        final = json.loads(recognizer.FinalResult()).get("text", "").strip()
        if final and (not chunks or final != chunks[-1]):
            chunks.append(final)
        text = " ".join(chunks).strip()
        if not text:
            raise RuntimeError("No clear speech was detected. Try again and speak close to the microphone.")
        return text
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Could not capture offline voice input: {exc}") from exc

def decision_from_text(text: str):
    """Return 'approve', 'reject', or None. Deliberately require a clear decision phrase."""
    normalized = re.sub(r"[^a-z ]", " ", (text or "").lower())
    normalized = " ".join(normalized.split())
    approve_phrases = {
    "yes", "yeah", "yep", "yes please", "yes do it",
    "approve", "approved", "approve it", "approve plan", "approve the plan",
    "yes approve", "yes approve it", "please approve the plan",
    "i approve", "i approve it", "proceed", "proceed with plan",
    "confirm", "confirm plan",
     }
    reject_phrases = {
    "no", "nope", "no thanks", "don't", "dont", "not now",
    "reject", "reject it", "reject the plan", "cancel", "cancel it",
    "cancel plan", "no reject", "do not approve", "dont approve", "stop",
     }
    if normalized in approve_phrases:
        return "approve"
    if normalized in reject_phrases:
        return "reject"
    return None

def listen_for_decision(timeout: int = 60, stop_event=None):
    """Listen for an explicit approval decision; return None on timeout/cancel."""
    sd, Model, KaldiRecognizer = _load_voice_dependencies()
    audio_queue = queue.Queue()
    model = Model(str(VOSK_MODEL_PATH))
    recognizer = KaldiRecognizer(model, 16000)

    def callback(indata, frames, time_info, status):
        audio_queue.put(bytes(indata))

    deadline = time.monotonic() + timeout
    try:
        with sd.RawInputStream(
            samplerate=16000, blocksize=8000, dtype="int16",
            channels=1, callback=callback
        ):
            while time.monotonic() < deadline:
                if stop_event is not None and stop_event.is_set():
                    return None
                try:
                    data = audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                if recognizer.AcceptWaveform(data):
                    text = json.loads(recognizer.Result()).get("text", "")
                    decision = decision_from_text(text)
                    if decision:
                        return decision
            final = json.loads(recognizer.FinalResult()).get("text", "")
            return decision_from_text(final)
    except Exception as exc:
        raise RuntimeError(f"Voice approval listening failed: {exc}") from exc
