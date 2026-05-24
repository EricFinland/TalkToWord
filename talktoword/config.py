"""User-configurable settings with startup management."""

import json
import os
import sys

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".talktoword")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

STARTUP_FOLDER = os.path.join(
    os.environ.get("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup",
)
STARTUP_SHORTCUT = os.path.join(STARTUP_FOLDER, "TalkToWord.bat")

DEFAULTS = {
    "hotkey": "ctrl+windows",
    "model_size": "base",
    "language": "en",
    "device": "auto",
    "recording_mode": "hold",   # "hold" or "toggle"
    "run_on_startup": False,
}

MODEL_OPTIONS = ["tiny", "base", "small", "medium", "large-v3"]
LANGUAGE_OPTIONS = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi",
}


def load() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            user = json.load(f)
        return {**DEFAULTS, **user}
    return DEFAULTS.copy()


def save(cfg: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    _sync_startup(cfg.get("run_on_startup", False))


def _get_launch_command() -> str:
    """Build the command that launches TalkToWord from its installed location."""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_python = os.path.join(project_dir, "venv", "Scripts", "pythonw.exe")
    run_script = os.path.join(project_dir, "run.py")

    if os.path.exists(venv_python):
        return f'@echo off\nstart "" "{venv_python}" "{run_script}"'

    return f'@echo off\nstart "" pythonw "{run_script}"'


def _sync_startup(enabled: bool) -> None:
    """Add or remove the startup shortcut."""
    if enabled:
        try:
            os.makedirs(STARTUP_FOLDER, exist_ok=True)
            with open(STARTUP_SHORTCUT, "w") as f:
                f.write(_get_launch_command())
        except OSError:
            pass
    else:
        try:
            if os.path.exists(STARTUP_SHORTCUT):
                os.remove(STARTUP_SHORTCUT)
        except OSError:
            pass


def is_startup_enabled() -> bool:
    return os.path.exists(STARTUP_SHORTCUT)
