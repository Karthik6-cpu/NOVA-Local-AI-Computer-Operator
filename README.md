# NOVA — Local AI Computer Operator (Windows MVP)

NOVA is a Windows desktop assistant designed to work without a mandatory cloud AI API key.
It uses a locally running Ollama model to interpret instructions and a separate allowlisted
execution layer to perform a small set of actions.

## What this version can do
- Desktop GUI with typed commands and optional push-to-talk voice input.
- Local AI planning through Ollama on `localhost`.
- Preview a structured plan; automatically listen for spoken `Approve` or `Reject` for 60 seconds, with a manual button fallback.
- Open Notepad, Calculator, File Explorer, Windows Settings, Task Manager, the default browser, WhatsApp Web, or an HTTP/HTTPS website.
- Discover and launch apps through Windows Start Menu shortcuts, and list available shortcut names.
- Open an existing folder by its absolute path.
- Create new text notes inside NOVA's own `workspace` directory.
- Search filenames inside that workspace.
- Keep a local JSONL audit log.

## Important limitations
- This is a starter MVP, not an unrestricted autonomous agent.
- It does not send WhatsApp messages, delete files, run arbitrary shell commands, or type into the active window.
- Local model quality and speed depend on your CPU, RAM, and the model selected.
- Ollama and the model must be installed/downloaded once. Afterward, local inference can work offline.
- Voice input is optional and uses a separately installed Vosk speech model.

## Recommended for a laptop with 8 GB RAM
Start with `qwen2.5:3b` in Ollama. It is a reasonable small-model starting point, but it may still use substantial memory alongside Windows. Close heavy applications if needed. If it is too slow or memory-hungry, try a smaller model available in Ollama, such as `qwen2.5:1.5b`.

## 1. Install Ollama and download a model
1. Install Ollama for Windows from https://ollama.com/download
2. Open PowerShell or Command Prompt.
3. Run:
   ```powershell
   ollama pull qwen2.5:3b
   ollama run qwen2.5:3b
   ```
4. Type a simple prompt to confirm it works, then exit the model chat with `/bye`.
5. Ollama normally runs a local service at `http://127.0.0.1:11434`.

Model download requires internet. After download, local inference does not require an AI API key.

## 2. Install NOVA
Extract the ZIP to a folder, then open that folder in PowerShell or VS Code terminal.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

You do **not** need to add an API key. `.env` only lets you change the local model and Ollama address.

If PowerShell blocks virtual environment activation, use:
```powershell
.\.venv\Scripts\python.exe main.py
```

## 3. Start NOVA
Make sure Ollama is installed and running, then:
```powershell
python main.py
```

Try:
- `Open Notepad`
- `Open Calculator`
- `Open File Explorer`
- `Open Settings`
- `Open Task Manager`
- `List applications`
- `Open Chrome` (if a Chrome shortcut exists in your Windows Start Menu)
- `Open WhatsApp`
- `Open https://www.python.org`
- `Create a note called DSA plan with text: revise arrays tomorrow`
- `Search files for report`

NOVA will create a plan locally. For plans with actions, it listens for spoken **Approve** or **Reject** for 60 seconds. You can still click **Approve and run plan** as a fallback.

## 4. Optional offline voice input
Voice requires the optional Vosk dependencies and model; typed commands work without it.

Install voice dependencies:
```powershell
pip install -r requirements-voice.txt
```

Download a Vosk English model from https://alphacephei.com/vosk/models (for example, a small English model), extract it, and place it in:
```text
models/vosk-model-small-en-us-0.15/
```
If you use a different model folder name, set `VOSK_MODEL_PATH` in `.env` to that folder path.
Then restart NOVA and use **Speak command**. Voice inference is local after the model is downloaded.

## Voice approval
When a plan with actions appears, NOVA opens a 60-second listening window for a clear phrase: `approve`, `approved`, `approve it`, `yes approve`, `proceed`, `confirm`, `reject`, `cancel`, or `stop`. Other speech is ignored. If the microphone/model cannot listen, use the manual approval button. Voice approval only approves the currently displayed plan.

## 5. Tests
Run:
```powershell
python -m unittest discover -s tests -v
```

## Project layout
```text
NOVA_Local_AI_Computer_Operator/
├── main.py
├── requirements.txt
├── requirements-voice.txt
├── .env.example
├── README.md
├── nova/
│   ├── __init__.py
│   ├── config.py
│   ├── planner.py
│   ├── safety.py
│   ├── tools.py
│   ├── voice.py
│   └── audit.py
├── tests/
│   └── test_safety.py
├── models/                  # optional Vosk model goes here
├── logs/                    # created at runtime
└── workspace/               # notes/search scope
```

## Safety model
- Local model output is treated as untrusted data.
- Tool names and argument schemas are validated in Python.
- No arbitrary shell commands or code execution.
- Only HTTP/HTTPS URLs are accepted.
- Notes are created only inside NOVA's workspace and existing notes are not overwritten.
- Every non-empty plan requires explicit approval; voice approval listens for a clear decision phrase for up to 60 seconds, with a manual button fallback.
- Action outcomes are logged locally.
- Do not use the app to send unwanted bulk messages or automate actions against a service in ways that violate its terms.

## Roadmap
1. Current package: local planner, GUI, allowlisted tools, approval, audit.
2. Add spoken responses and a wake-word mode.
3. Add Windows UI Automation and action verification for keyboard/mouse control.
4. Add WhatsApp message preparation with contact verification and a confirmation step before sending.
5. Add local document reading/retrieval and automated evaluation tests.
