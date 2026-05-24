"""Inject transcribed text into the currently focused application."""

import time
import pyperclip
import keyboard


def type_text(text: str) -> None:
    """
    Paste text into whichever window/text field is currently focused.

    Uses clipboard paste (Ctrl+V) instead of simulating individual keystrokes
    because it's instant and handles special characters, unicode, etc.
    The original clipboard contents are saved and restored afterward.
    """
    if not text:
        return

    original = _safe_get_clipboard()

    pyperclip.copy(text)
    time.sleep(0.05)
    keyboard.send("ctrl+v")
    time.sleep(0.1)

    # Restore original clipboard
    if original is not None:
        pyperclip.copy(original)


def _safe_get_clipboard() -> str | None:
    try:
        return pyperclip.paste()
    except Exception:
        return None
