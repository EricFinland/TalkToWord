"""Small floating status bar overlay — always on top, shows recording state."""

import tkinter as tk
import threading


class OverlayBar:
    """
    A tiny draggable pill that sits at the top-center of the screen.
    Green = idle, Red = recording, Orange = processing.
    """

    WIDTH = 180
    HEIGHT = 32
    CORNER_RADIUS = 16

    COLOR_IDLE = "#4CAF50"
    COLOR_RECORDING = "#F44336"
    COLOR_PROCESSING = "#FF9800"
    TEXT_COLOR = "white"

    def __init__(self):
        self._root: tk.Tk | None = None
        self._canvas: tk.Canvas | None = None
        self._text_id = None
        self._pill_id = None
        self._dot_id = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._drag_data = {"x": 0, "y": 0}

    def start(self) -> None:
        self._thread = threading.Thread(target=self._build, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)

    def _build(self) -> None:
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.88)
        self._root.lift()

        # Transparent background (Windows)
        self._root.config(bg="SystemButtonFace")
        try:
            self._root.attributes("-transparentcolor", "SystemButtonFace")
        except tk.TclError:
            pass

        screen_w = self._root.winfo_screenwidth()
        x = (screen_w - self.WIDTH) // 2
        y = 8
        self._root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self._canvas = tk.Canvas(
            self._root,
            width=self.WIDTH,
            height=self.HEIGHT,
            highlightthickness=0,
            bg="SystemButtonFace",
        )
        self._canvas.pack()

        self._pill_id = self._rounded_rect(
            2, 2, self.WIDTH - 2, self.HEIGHT - 2,
            self.CORNER_RADIUS, fill=self.COLOR_IDLE, outline=""
        )

        self._dot_id = self._canvas.create_oval(
            12, 10, 22, 20, fill=self.TEXT_COLOR, outline=""
        )

        self._text_id = self._canvas.create_text(
            self.WIDTH // 2 + 6, self.HEIGHT // 2,
            text="Ready", fill=self.TEXT_COLOR,
            font=("Segoe UI", 9, "bold"),
        )

        self._canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self._canvas.bind("<B1-Motion>", self._on_drag_motion)

        self._ready.set()
        self._root.mainloop()

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        return self._canvas.create_polygon(points, smooth=True, **kwargs)

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        if self._root:
            dx = event.x - self._drag_data["x"]
            dy = event.y - self._drag_data["y"]
            x = self._root.winfo_x() + dx
            y = self._root.winfo_y() + dy
            self._root.geometry(f"+{x}+{y}")

    def set_recording(self) -> None:
        if self._root and self._canvas:
            self._root.after(0, self._update, self.COLOR_RECORDING, "Recording…")

    def set_processing(self) -> None:
        if self._root and self._canvas:
            self._root.after(0, self._update, self.COLOR_PROCESSING, "Transcribing…")

    def set_idle(self) -> None:
        if self._root and self._canvas:
            self._root.after(0, self._update, self.COLOR_IDLE, "Ready")

    def _update(self, color: str, text: str) -> None:
        if self._canvas and self._pill_id:
            self._canvas.itemconfig(self._pill_id, fill=color)
        if self._canvas and self._text_id:
            self._canvas.itemconfig(self._text_id, text=text)

    def stop(self) -> None:
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
