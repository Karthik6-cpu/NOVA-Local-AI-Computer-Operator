from urllib.parse import urlparse
from pathlib import Path
import os

ALLOWED_TOOLS = {
    "open_notepad", "open_calculator", "open_whatsapp", "open_url",
    "create_note", "search_files", "open_file_explorer", "open_settings",
    "open_task_manager", "open_browser", "open_application", "list_applications",
    "open_folder",
}

def validate_url(url: str) -> str:
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError("URL must be a string shorter than 2048 characters.")
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Only complete HTTP or HTTPS URLs are allowed.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing embedded credentials are not allowed.")
    return url.strip()

def validate_action(action: dict) -> tuple[str, dict]:
    if not isinstance(action, dict):
        raise ValueError("Action must be an object.")
    tool, args = action.get("tool"), action.get("args", {})
    if tool not in ALLOWED_TOOLS:
        raise ValueError(f"Tool is not allowed: {tool!r}")
    if not isinstance(args, dict):
        raise ValueError("Action args must be an object.")
    schemas = {
        "open_notepad": set(),
        "open_calculator": set(),
        "open_whatsapp": set(),
        "open_url": {"url"},
        "create_note": {"title", "content"},
        "search_files": {"query"},
        "open_file_explorer": set(),
        "open_settings": set(),
        "open_task_manager": set(),
        "open_browser": set(),
        "open_application": {"name"},
        "list_applications": set(),
        "open_folder": {"path"},
    }
    if set(args) != schemas[tool]:
        raise ValueError(f"Incorrect arguments for {tool}. Expected: {sorted(schemas[tool])}")
    if tool == "open_url":
        args = {"url": validate_url(args["url"])}
    elif tool == "create_note":
        title, content = args["title"], args["content"]
        if not isinstance(title, str) or not isinstance(content, str):
            raise ValueError("Note title/content must be text.")
        if not title.strip() or len(title) > 100 or len(content) > 10000:
            raise ValueError("Note title/content is empty or too long.")
        if any(c in title for c in r'\/:*?"<>|') or title.strip() in {".", ".."}:
            raise ValueError("Note title contains characters not allowed in filenames.")
    elif tool == "search_files":
        query = args["query"]
        if not isinstance(query, str) or not query.strip() or len(query) > 100:
            raise ValueError("Search query must be 1–100 characters.")
    elif tool == "open_application":
        name = args["name"]
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            raise ValueError("Application name must be 1–100 characters.")
        if any(c in name for c in r'\/:*?"<>|'):
            raise ValueError("Enter an application name, not a path or command.")
        args = {"name": name.strip()}
    elif tool == "open_folder":
        path = args["path"]
        if not isinstance(path, str) or not path.strip() or len(path) > 500:
            raise ValueError("Folder path must be 1–500 characters.")
        if not os.path.isabs(path):
            raise ValueError("Folder path must be absolute.")
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise ValueError("That folder does not exist or is not a directory.")
        args = {"path": str(resolved)}
    return tool, args
