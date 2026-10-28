import os
import subprocess
import webbrowser
from pathlib import Path
import json

from nova.config import WORKSPACE
from nova.safety import validate_action

WHATSAPP_URL = "https://web.whatsapp.com"
START_MENU_ROOTS = [
    Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Microsoft/Windows/Start Menu/Programs",
    Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
]
BUILTIN_APPS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "task manager": ["taskmgr.exe"],
    "file explorer": ["explorer.exe"],
}

def _start_menu_shortcuts():
    found = []
    for base in START_MENU_ROOTS:
        if base.exists():
            try:
                found.extend(p for p in base.rglob("*.lnk") if p.is_file())
            except OSError:
                pass
    return found

def _normalize_name(value):
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _launch_application(name):
    if os.name != "nt":
        return {
            "ok": False,
            "message": "Application launching is supported on Windows only."
        }

    requested = name.strip()
    key = _normalize_name(requested)

    if not key:
        return {"ok": False, "message": "Please specify an application name."}

    # 1. Try known safe Windows executable aliases.
    for alias, command in BUILTIN_APPS.items():
        if key == _normalize_name(alias):
            try:
                subprocess.Popen(command, shell=False)
                return {"ok": True, "message": f"Opened {alias.title()}."}
            except OSError as exc:
                return {"ok": False, "message": f"Could not open {alias}: {exc}"}

    # 2. Prefer an exact Start Menu shortcut match.
    try:
        shortcuts = _start_menu_shortcuts()
        exact = [p for p in shortcuts if _normalize_name(p.stem) == key]

        if len(exact) == 1:
            os.startfile(str(exact[0]))
            return {"ok": True, "message": f"Opened {exact[0].stem}."}

        if len(exact) > 1:
            choices = sorted({p.stem for p in exact}, key=str.casefold)
            return {
                "ok": False,
                "message": "Multiple exact matches found: " + ", ".join(choices[:10])
            }
    except OSError:
        pass

    # 3. Try Windows packaged apps registered with Get-StartApps.
    # The application name is matched against Windows' own app registry.
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json -Compress"
            ],
            capture_output=True,
            text=True,
            timeout=15,
            shell=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        if result.returncode == 0 and result.stdout.strip():
            apps = json.loads(result.stdout)
            if isinstance(apps, dict):
                apps = [apps]

            exact_apps = [
                app for app in apps
                if isinstance(app, dict)
                and _normalize_name(str(app.get("Name", ""))) == key
                and isinstance(app.get("AppID"), str)
            ]

            if len(exact_apps) == 1:
                app_id = exact_apps[0]["AppID"]

                # Pass the validated app ID as a parameter; do not build
                # or execute a command from the requested app name.
                launch_script = (
                    "param([string]$AppId); "
                    "Start-Process -FilePath 'explorer.exe' "
                    "-ArgumentList @('shell:AppsFolder\\' + $AppId)"
                )
                launch = subprocess.run(
                    [
                        "powershell.exe", "-NoProfile", "-NonInteractive",
                        "-Command", launch_script, app_id
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    shell=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )

                if launch.returncode == 0:
                    return {
                        "ok": True,
                        "message": f"Requested Windows to open {exact_apps[0]['Name']}."
                    }

                return {
                    "ok": False,
                    "message": f"Windows could not launch {requested!r}."
                }

    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # 4. If there is no exact match, report possible shortcut matches.
    try:
        shortcuts = _start_menu_shortcuts()
        matches = [
            p for p in shortcuts
            if key in _normalize_name(p.stem)
        ]
        matches = list({str(p): p for p in matches}.values())

        if len(matches) == 1:
            os.startfile(str(matches[0]))
            return {"ok": True, "message": f"Opened {matches[0].stem}."}

        if len(matches) > 1:
            choices = sorted({p.stem for p in matches}, key=str.casefold)
            return {
                "ok": False,
                "message": "Several apps matched. Try a more specific name: "
                + ", ".join(choices[:10])
            }
    except OSError:
        pass

    return {
        "ok": False,
        "message": (
            f"Couldn't find an exact installed application named {requested!r}. "
            "Try 'list applications' to see available shortcuts."
        )
    }

def execute_action(action: dict) -> dict:
    try:
        tool, args = validate_action(action)
        if tool == "open_notepad":
            if os.name != "nt":
                return {"ok": False, "message": "Notepad is supported on Windows only."}
            subprocess.Popen(["notepad.exe"], shell=False)
            return {"ok": True, "message": "Opened Notepad."}
        if tool == "open_calculator":
            if os.name != "nt":
                return {"ok": False, "message": "Calculator is supported on Windows only."}
            subprocess.Popen(["calc.exe"], shell=False)
            return {"ok": True, "message": "Opened Calculator."}
        if tool == "open_file_explorer":
            if os.name != "nt":
                return {"ok": False, "message": "File Explorer is supported on Windows only."}
            subprocess.Popen(["explorer.exe"], shell=False)
            return {"ok": True, "message": "Opened File Explorer."}
        if tool == "open_settings":
            if os.name != "nt":
                return {"ok": False, "message": "Windows Settings is supported on Windows only."}
            os.startfile("ms-settings:")
            return {"ok": True, "message": "Opened Windows Settings."}
        if tool == "open_task_manager":
            if os.name != "nt":
                return {"ok": False, "message": "Task Manager is supported on Windows only."}
            subprocess.Popen(["taskmgr.exe"], shell=False)
            return {"ok": True, "message": "Opened Task Manager."}
        if tool == "open_browser":
            webbrowser.open("https://www.google.com")
            return {"ok": True, "message": "Opened your default browser."}
        if tool == "open_application":
            return _launch_application(args["name"])
        if tool == "list_applications":
            names = sorted({p.stem for p in _start_menu_shortcuts()}, key=str.casefold)
            if not names:
                return {"ok": True, "message": "No Start Menu shortcuts were found. You can still open Notepad, Calculator, File Explorer, Settings, Task Manager, and the default browser."}
            return {"ok": True, "message": "Apps found in the Windows Start Menu (some may be shortcuts or folders):\n" + "\n".join(names[:100])}
        if tool == "open_folder":
            os.startfile(args["path"])
            return {"ok": True, "message": f"Opened folder: {args['path']}"}
        if tool == "open_whatsapp":
            webbrowser.open(WHATSAPP_URL)
            return {"ok": True, "message": "Opened WhatsApp Web. No message was sent."}
        if tool == "open_url":
            webbrowser.open(args["url"])
            return {"ok": True, "message": f"Opened {args['url']}"}
        if tool == "create_note":
            WORKSPACE.mkdir(parents=True, exist_ok=True)
            path = (WORKSPACE / (args["title"].strip() + ".txt")).resolve()
            if path.parent != WORKSPACE.resolve():
                return {"ok": False, "message": "Blocked: note path escaped the NOVA workspace."}
            if path.exists():
                return {"ok": False, "message": "A note with that name already exists; nothing overwritten."}
            path.write_text(args["content"], encoding="utf-8")
            return {"ok": True, "message": f"Created {path.name} inside the NOVA workspace."}
        if tool == "search_files":
            WORKSPACE.mkdir(parents=True, exist_ok=True)
            query = args["query"].casefold()
            matches = []
            for path in WORKSPACE.rglob("*"):
                if path.is_file() and query in path.name.casefold():
                    matches.append(path.relative_to(WORKSPACE).as_posix())
                    if len(matches) >= 20:
                        break
            if not matches:
                return {"ok": True, "message": f"No filenames matched {args['query']!r} in the NOVA workspace."}
            return {"ok": True, "message": "Matching files:\n" + "\n".join(matches)}
        return {"ok": False, "message": "No executor exists for this tool."}
    except Exception as exc:
        return {"ok": False, "message": f"Blocked or failed: {exc}"}

def execute_plan(plan: dict) -> list[dict]:
    actions = plan.get("actions", [])
    if not isinstance(actions, list) or len(actions) > 5:
        raise ValueError("Invalid plan.")
    results = []
    for action in actions:
        result = execute_action(action)
        results.append(result)
        if not result["ok"]:
            results.append({"ok": False, "message": "Stopped remaining actions after a failure."})
            break
    return results
