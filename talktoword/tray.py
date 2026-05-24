"""System tray icon — lives in the ^ caret area, shows app status."""

import threading
from PIL import Image, ImageDraw
import pystray


class TrayIcon:
    COLOR_IDLE = "#4CAF50"
    COLOR_RECORDING = "#F44336"
    COLOR_PROCESSING = "#FF9800"

    def __init__(self, on_quit=None, on_settings=None, **_kwargs):
        self._on_quit = on_quit
        self._on_settings = on_settings
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None
        self._hotkey_label = "Ctrl+Win"

    def start(self, hotkey_label: str = "Ctrl+Win") -> None:
        self._hotkey_label = hotkey_label

        menu = pystray.Menu(
            pystray.MenuItem("TalkToWord", None, enabled=False),
            pystray.MenuItem(
                f"Hold {hotkey_label} to record", None, enabled=False,
            ),
            pystray.MenuItem(
                f"Double-tap to lock recording", None, enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings…", self._open_settings),
            pystray.MenuItem("Quit", self._quit),
        )

        self._icon = pystray.Icon(
            "TalkToWord",
            self._make_icon(self.COLOR_IDLE),
            f"TalkToWord — Ready ({self._hotkey_label})",
            menu,
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def set_recording(self) -> None:
        if self._icon:
            self._icon.icon = self._make_icon(self.COLOR_RECORDING)
            self._icon.title = "TalkToWord — Recording…"

    def set_processing(self) -> None:
        if self._icon:
            self._icon.icon = self._make_icon(self.COLOR_PROCESSING)
            self._icon.title = "TalkToWord — Transcribing…"

    def set_idle(self) -> None:
        if self._icon:
            self._icon.icon = self._make_icon(self.COLOR_IDLE)
            self._icon.title = f"TalkToWord — Ready ({self._hotkey_label})"

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()

    def _open_settings(self, icon, item) -> None:
        if self._on_settings:
            self._on_settings()

    def _quit(self, icon, item) -> None:
        icon.stop()
        if self._on_quit:
            self._on_quit()

    @staticmethod
    def _make_icon(color: str, size: int = 64) -> Image.Image:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        margin = 4
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=color,
        )
        cx, cy = size // 2, size // 2
        r = size // 6
        draw.rounded_rectangle(
            [cx - r, cy - r - 4, cx + r, cy + r - 2],
            radius=r, fill="white",
        )
        draw.line([cx, cy + r - 2, cx, cy + r + 6], fill="white", width=3)
        draw.arc(
            [cx - r - 2, cy - 2, cx + r + 2, cy + r + 4],
            start=0, end=180, fill="white", width=2,
        )
        return img
