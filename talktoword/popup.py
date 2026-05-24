"""Tiny recording indicator — small pill at bottom-center of screen."""

import tkinter as tk
import threading
import math


class RecordingPopup:
    """
    A minimal pill (~160x36) that appears at the bottom-center of the screen
    only while recording. Shows a small pulsing red dot + text.
    """

    W = 160
    H = 36
    MARGIN_BOTTOM = 60

    BG = "#1a1a1a"
    DOT_COLOR = "#e94560"
    TEXT_COLOR = "#e0e0e0"
    PROCESSING_DOT = "#f0a500"

    def __init__(self):
        self._root: tk.Tk | None = None
        self._canvas: tk.Canvas | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._visible = False
        self._animating = False
        self._phase = 0.0
        self._dot_id = None
        self._text_id = None
        self._bg_id = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._build, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)

    def _build(self) -> None:
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.withdraw()

        try:
            self._root.attributes("-transparentcolor", "#010101")
        except tk.TclError:
            pass

        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        x = (screen_w - self.W) // 2
        y = screen_h - self.H - self.MARGIN_BOTTOM
        self._root.geometry(f"{self.W}x{self.H}+{x}+{y}")

        self._canvas = tk.Canvas(
            self._root, width=self.W, height=self.H,
            highlightthickness=0, bg="#010101",
        )
        self._canvas.pack()

        r = self.H // 2
        self._bg_id = self._canvas.create_polygon(
            r, 2, self.W - r, 2, self.W - 2, 2, self.W - 2, r,
            self.W - 2, self.H - r, self.W - 2, self.H - 2,
            self.W - r, self.H - 2, r, self.H - 2, 2, self.H - 2,
            2, self.H - r, 2, r, 2, 2,
            smooth=True, fill=self.BG, outline="#333333",
        )

        cy = self.H // 2
        self._dot_id = self._canvas.create_oval(
            14, cy - 5, 24, cy + 5,
            fill=self.DOT_COLOR, outline="",
        )

        self._text_id = self._canvas.create_text(
            90, cy, text="Listening…",
            fill=self.TEXT_COLOR, font=("Segoe UI", 9),
        )

        self._ready.set()
        self._root.mainloop()

    def show_recording(self, locked: bool = False) -> None:
        if not self._root:
            return
        self._root.after(0, self._do_show, locked)

    def show_processing(self) -> None:
        if not self._root:
            return
        self._root.after(0, self._do_show_processing)

    def hide(self) -> None:
        if not self._root:
            return
        self._root.after(0, self._do_hide)

    def _do_show(self, locked: bool) -> None:
        self._animating = True
        self._visible = True
        label = "Locked on…" if locked else "Listening…"
        self._canvas.itemconfig(self._text_id, text=label, fill=self.TEXT_COLOR)
        self._canvas.itemconfig(self._dot_id, fill=self.DOT_COLOR)
        self._root.deiconify()
        self._root.attributes("-alpha", 0.9)
        self._phase = 0.0
        self._pulse()

    def _do_show_processing(self) -> None:
        self._animating = False
        self._visible = True
        self._canvas.itemconfig(self._text_id, text="Transcribing…", fill=self.PROCESSING_DOT)
        self._canvas.itemconfig(self._dot_id, fill=self.PROCESSING_DOT)
        self._root.deiconify()

    def _do_hide(self) -> None:
        self._animating = False
        self._visible = False
        self._root.withdraw()

    def _pulse(self) -> None:
        if not self._animating or not self._visible:
            return
        self._phase += 0.12
        brightness = 0.5 + 0.5 * math.sin(self._phase)
        r = int(180 + 75 * brightness)
        g = int(30 + 39 * brightness)
        b = int(60 + 36 * brightness)
        self._canvas.itemconfig(self._dot_id, fill=f"#{r:02x}{g:02x}{b:02x}")
        self._root.after(50, self._pulse)

    def stop(self) -> None:
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
