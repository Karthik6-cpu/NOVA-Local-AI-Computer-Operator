# NOVA --- Local AI Computer Operator

NOVA is a local AI desktop assistant for Windows that turns
natural-language requests into computer actions. It is designed to use
Ollama for local language-model inference and Vosk for offline speech
recognition.

> **Safety first:** NOVA asks for confirmation before executing actions
> through its desktop interface. Review each requested action before
> approving it.

## Features

-   **Natural-language planning** --- converts requests into structured
    action plans.
-   **Local language model** --- configured by default to use
    `qwen2.5:3b` through Ollama.
-   **Voice input support** --- uses Vosk when the optional voice
    dependencies and model are installed.
-   **Desktop actions** --- supports tools for opening applications,
    Notepad, Calculator, File Explorer, Settings, Task Manager, a
    browser, and WhatsApp.
-   **Web navigation** --- opens URLs in the browser.
-   **File utilities** --- searches for files and opens folders.
-   **Notes** --- creates notes through the application's supported note
    workflow.
-   **Safety checks** --- validates allowed tools and checks folder
    paths before actions are executed.
-   **Audit logging** --- records supported activity in a local log
    file.

Available behavior depends on your configuration, installed
dependencies, and Windows environment.

## Project structure

  Path                Purpose
  ------------------- ------------------------------------------------
  `main.py`           Desktop application entry point
  `nova/planner.py`   Converts requests into structured action plans
  `nova/tools.py`     Implements supported computer actions
  `nova/safety.py`    Applies tool allow-list and safety validation
  `nova/config.py`    Loads application configuration
  `nova/voice.py`     Voice-input support
  `nova/audit.py`     Local audit logging
  `tests/`            Automated tests

## Requirements

-   Windows 10 or Windows 11
-   A Python version compatible with the packages in `requirements.txt`
-   [Git](https://git-scm.com/downloads)
-   [Ollama](https://ollama.com/download), installed and running locally
-   The configured Ollama model, `qwen2.5:3b`
-   For voice input: packages in `requirements-voice.txt` and a Vosk
    model

## Setup

### 1. Clone the repository

``` powershell
git clone https://github.com/Karthik6-cpu/NOVA-Local-AI-Computer-Operator.git
cd NOVA-Local-AI-Computer-Operator
```

### 2. Create and activate a virtual environment

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, allow it for the current terminal
session:

``` powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

``` powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For voice features, install the optional dependencies:

``` powershell
pip install -r requirements-voice.txt
```

### 4. Install and prepare Ollama

Install Ollama from [ollama.com/download](https://ollama.com/download),
start it, and download the configured model:

``` powershell
ollama pull qwen2.5:3b
```

The default local endpoint is `http://127.0.0.1:11434`. Ensure Ollama is
running before launching NOVA.

### 5. Configure the environment

Create your local environment file from the example:

``` powershell
Copy-Item .env.example .env
```

The example configuration uses:

``` dotenv
NOVA_MODEL=qwen2.5:3b
OLLAMA_URL=http://127.0.0.1:11434
NOVA_WORKSPACE=workspace
VOSK_MODEL_PATH=models/vosk-model-small-en-us-0.15
```

The Vosk model itself is not included in this repository. Download a
suitable model from the [Vosk models
page](https://alphacephei.com/vosk/models), extract it under `models/`,
and ensure `VOSK_MODEL_PATH` matches the extracted directory. Review its
license and terms before redistribution.

### 6. Launch NOVA

From the project root, with the virtual environment activated and Ollama
running:

``` powershell
python main.py
```

## Safety and privacy

-   Review every proposed action and approve it only when you understand
    what it will do.
-   Keep `.env`, audit logs, local databases, and personal workspace
    files out of public repositories.
-   Never store API keys, passwords, or other secrets in source files.
-   Use file and folder actions only on locations you trust.
-   Local inference reduces reliance on cloud model APIs, but it does
    not automatically guarantee that every component of your system is
    private. Review your OS settings and installed dependencies.

## Tests

Run the tests from the project root:

``` powershell
python -m pytest
```

If `pytest` is not installed, install it in your active virtual
environment first.

## Troubleshooting

### Ollama connection error

1.  Make sure Ollama is installed and running.

2.  Check that `OLLAMA_URL` is `http://127.0.0.1:11434`, unless you
    intentionally use another endpoint.

3.  List locally available models:

    ``` powershell
    ollama list
    ```

4.  If needed, download the configured model:

    ``` powershell
    ollama pull qwen2.5:3b
    ```

### Voice input is unavailable

1.  Install optional voice dependencies using
    `pip install -r requirements-voice.txt`.
2.  Confirm `VOSK_MODEL_PATH` points to an extracted Vosk model
    directory.
3.  Check microphone permissions in Windows settings.

### An application does not open

Confirm the application is installed and available on your system.
Application names and launch behavior can vary between Windows
installations.

## Project status

NOVA is an actively developed personal project. Some capabilities
require local setup and may behave differently across Windows systems.
Test actions carefully before relying on them.

## Contributing

Suggestions, bug reports, and pull requests are welcome. Include clear
reproduction steps for issues, and avoid attaching logs that may contain
private information.

## License

No license is specified in this repository yet. Unless a license is
added, reuse, modification, and redistribution are not automatically
granted. Add a suitable `LICENSE` file if you intend to publish the
project under an open-source license.

## Author

**Karthik6-cpu**

-   GitHub: [Karthik6-cpu](https://github.com/Karthik6-cpu)
-   Repository: [NOVA --- Local AI Computer
    Operator](https://github.com/Karthik6-cpu/NOVA-Local-AI-Computer-Operator)
