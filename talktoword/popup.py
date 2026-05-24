"""Recording popup — appears only while recording, with pulsing mic animation."""

import tkinter as tk
import threading
import math


class RecordingPopup:
    """
    A small centered popup that appears when recording starts and
    disappears when recording stops. Shows an animated pulsing ring
    around a microphone icon to indicate it's actively listening.
    """

    SIZE = 120
    BG = "#1a1a2e"
    RING_COLOR_START = "#e94560"
    RING_COLOR_PULSE = "#ff6b6b"
    MIC_COLOR = "white"
    TEXT_COLOR = "#cccccc"
    PROCESSING_BG = "#16213e"
    PROCESSING_COLOR = "#f0a500"

    def __init__(self):
        self._root: tk.Tk | None = None
        self._canvas: tk.Canvas | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._visible = False
        self._animating = False
        self._pulse_phase = 0.0
        self._ring_ids: list = []
        self._mic_ids: list = []
        self._text_id = None
        self._mode_text_id = None
        self._bg_rect = None

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

        w, h = self.SIZE + 60, self.SIZE + 50
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2 - 80
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        self._canvas = tk.Canvas(
            self._root, width=w, height=h,
            highlightthickness=0, bg="#010101",
        )
        self._canvas.pack()

        self._bg_rect = self._rounded_rect(
            4, 4, w - 4, h - 4, 20, fill=self.BG, outline=""
        )

        cx = w // 2
        cy = (h - 24) // 2

        # Pulsing rings (3 layers)
        for i in range(3):
            rid = self._canvas.create_oval(0, 0, 0, 0, outline=self.RING_COLOR_START, width=2)
            self._ring_ids.append(rid)

        # Microphone body
        self._mic_ids.append(
            self._canvas.create_oval(cx - 14, cy - 22, cx + 14, cy + 6, fill=self.MIC_COLOR, outline="")
        )
        # Mic stem
        self._mic_ids.append(
            self._canvas.create_line(cx, cy + 6, cx, cy + 20, fill=self.MIC_COLOR, width=3)
        )
        # Mic base
        self._mic_ids.append(
            self._canvas.create_line(cx - 10, cy + 20, cx + 10, cy + 20, fill=self.MIC_COLOR, width=3)
        )
        # Mic arc
        self._mic_ids.append(
            self._canvas.create_arc(
                cx - 20, cy - 10, cx + 20, cy + 14,
                start=0, extent=-180, style="arc",
                outline=self.MIC_COLOR, width=2.5,
            )
        )

        self._text_id = self._canvas.create_text(
            cx, h - 22, text="Listening…",
            fill=self.TEXT_COLOR, font=("Segoe UI", 9),
        )

        self._mode_text_id = self._canvas.create_text(
            cx, h - 8, text="",
            fill="#666666", font=("Segoe UI", 7),
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
        self._canvas.itemconfig(self._bg_rect, fill=self.BG)
        self._canvas.itemconfig(self._text_id, text="Listening…", fill=self.TEXT_COLOR)
        mode_label = "locked — tap hotkey to stop" if locked else "release to finish"
        self._canvas.itemconfig(self._mode_text_id, text=mode_label)
        for mid in self._mic_ids:
            self._canvas.itemconfig(mid, fill=self.MIC_COLOR)
        self._root.deiconify()
        self._root.attributes("-alpha", 0.92)
        self._pulse_phase = 0.0
        self._animate_pulse()

    def _do_show_processing(self) -> None:
        self._animating = False
        self._visible = True
        self._canvas.itemconfig(self._bg_rect, fill=self.PROCESSING_BG)
        self._canvas.itemconfig(self._text_id, text="Transcribing…", fill=self.PROCESSING_COLOR)
        self._canvas.itemconfig(self._mode_text_id, text="")
        for rid in self._ring_ids:
            self._canvas.itemconfig(rid, outline="")
        self._root.deiconify()

    def _do_hide(self) -> None:
        self._animating = False
        self._visible = False
        self._root.withdraw()

    def _animate_pulse(self) -> None:
        if not self._animating or not self._visible:
            return

        w = self.SIZE + 60
        h = self.SIZE + 50
        cx = w // 2
        cy = (h - 24) // 2
        self._pulse_phase += 0.08

        for i, rid in enumerate(self._ring_ids):
            phase = self._pulse_phase - (i * 0.7)
            scale = 0.5 + 0.5 * max(0, math.sin(phase))
            r = 28 + scale * 18
            alpha_val = max(0, math.sin(phase))
            r_int = int(233 + (255 - 233) * alpha_val)
            g_int = int(69 + (107 - 69) * alpha_val)
            b_int = int(96 + (107 - 96) * alpha_val)
            color = f"#{r_int:02x}{g_int:02x}{b_int:02x}"
            width = 1.5 + alpha_val * 1.5

            self._canvas.coords(rid, cx - r, cy - 8 - r + 16, cx + r, cy - 8 + r + 16)
            self._canvas.itemconfig(rid, outline=color, width=width)

        self._root.after(40, self._animate_pulse)

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return self._canvas.create_polygon(points, smooth=True, **kwargs)

    def stop(self) -> None:
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
