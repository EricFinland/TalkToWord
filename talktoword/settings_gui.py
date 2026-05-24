"""Settings window built with tkinter (ships with Python, no extra deps)."""

import tkinter as tk
from tkinter import ttk
import threading

from talktoword import config


class SettingsWindow:

    def __init__(self, current_cfg: dict, on_save: callable = None):
        self._cfg = current_cfg.copy()
        self._on_save = on_save
        self._root: tk.Tk | None = None

    def open(self) -> None:
        thread = threading.Thread(target=self._build_and_run, daemon=True)
        thread.start()

    def _build_and_run(self) -> None:
        self._root = tk.Tk()
        self._root.title("TalkToWord — Settings")
        self._root.resizable(False, False)
        self._root.attributes("-topmost", True)
        self._root.iconphoto(False, tk.PhotoImage(width=1, height=1))

        style = ttk.Style(self._root)
        style.theme_use("clam")

        main = ttk.Frame(self._root, padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="TalkToWord Settings", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 16), sticky="w"
        )

        row = 1

        # ── Hotkey ──
        ttk.Label(main, text="Hotkey:").grid(row=row, column=0, sticky="w", pady=6)
        self._hotkey_var = tk.StringVar(value=self._cfg["hotkey"])
        ttk.Entry(main, textvariable=self._hotkey_var, width=28).grid(
            row=row, column=1, sticky="w", pady=6, padx=(8, 0)
        )
        row += 1

        # ── Usage hint ──
        ttk.Label(
            main, text="Hold = record while held  |  Double-tap = lock on",
            font=("Segoe UI", 8), foreground="#888888",
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 8))
        row += 1

        # ── Model size ──
        ttk.Label(main, text="Whisper model:").grid(row=row, column=0, sticky="w", pady=6)
        self._model_var = tk.StringVar(value=self._cfg["model_size"])
        ttk.Combobox(
            main, textvariable=self._model_var,
            values=config.MODEL_OPTIONS, state="readonly", width=25,
        ).grid(row=row, column=1, sticky="w", pady=6, padx=(8, 0))
        row += 1

        # ── Language ──
        ttk.Label(main, text="Language:").grid(row=row, column=0, sticky="w", pady=6)
        lang_display = [f"{v} ({k})" for k, v in config.LANGUAGE_OPTIONS.items()]
        current_lang = config.LANGUAGE_OPTIONS.get(self._cfg["language"], "English")
        self._lang_var = tk.StringVar(value=f"{current_lang} ({self._cfg['language']})")
        ttk.Combobox(
            main, textvariable=self._lang_var,
            values=lang_display, state="readonly", width=25,
        ).grid(row=row, column=1, sticky="w", pady=6, padx=(8, 0))
        row += 1

        # ── Device ──
        ttk.Label(main, text="Device:").grid(row=row, column=0, sticky="w", pady=6)
        self._device_var = tk.StringVar(value=self._cfg["device"])
        ttk.Combobox(
            main, textvariable=self._device_var,
            values=["auto", "cpu", "cuda"], state="readonly", width=25,
        ).grid(row=row, column=1, sticky="w", pady=6, padx=(8, 0))
        row += 1

        # ── Run on startup ──
        self._startup_var = tk.BooleanVar(value=self._cfg.get("run_on_startup", False))
        ttk.Checkbutton(
            main, text="Run TalkToWord on Windows startup",
            variable=self._startup_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(12, 6))
        row += 1

        # ── Buttons ──
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(16, 0), sticky="e")
        ttk.Button(btn_frame, text="Cancel", command=self._root.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="right")

        self._root.update_idletasks()
        w = self._root.winfo_width()
        h = self._root.winfo_height()
        x = (self._root.winfo_screenwidth() // 2) - (w // 2)
        y = (self._root.winfo_screenheight() // 2) - (h // 2)
        self._root.geometry(f"+{x}+{y}")

        self._root.mainloop()

    def _save(self) -> None:
        lang_raw = self._lang_var.get()
        lang_code = lang_raw.split("(")[-1].rstrip(")").strip() if "(" in lang_raw else "en"

        new_cfg = {
            "hotkey": self._hotkey_var.get().strip(),
            "model_size": self._model_var.get(),
            "language": lang_code,
            "device": self._device_var.get(),
            "run_on_startup": self._startup_var.get(),
        }

        needs_reload = (
            new_cfg["hotkey"] != self._cfg["hotkey"]
            or new_cfg["model_size"] != self._cfg["model_size"]
            or new_cfg["device"] != self._cfg["device"]
            or new_cfg["language"] != self._cfg["language"]
        )

        config.save(new_cfg)

        if self._root:
            self._root.destroy()

        if needs_reload and self._on_save:
            self._on_save(new_cfg)
