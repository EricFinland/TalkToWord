"""Main application — two recording modes, settings GUI, startup support."""

import os
import sys
import time
import threading
import keyboard

from talktoword import config
from talktoword.recorder import AudioRecorder
from talktoword.transcriber import Transcriber
from talktoword.typer import type_text
from talktoword.tray import TrayIcon
from talktoword.overlay import OverlayBar
from talktoword.settings_gui import SettingsWindow


class TalkToWordApp:
    def __init__(self):
        self.cfg = config.load()
        self.recorder = AudioRecorder()
        self.transcriber: Transcriber | None = None
        self.tray = TrayIcon(
            on_quit=self.shutdown,
            on_settings=self._open_settings,
            get_mode=lambda: self.cfg["recording_mode"],
            set_mode=self._set_mode,
        )
        self.overlay: OverlayBar | None = None
        self._running = True
        self._busy = False
        self._held = False  # tracks whether hotkey is physically held down

    # ── public ────────────────────────────────────────────────────────

    def run(self) -> None:
        print("=" * 50)
        print("  TalkToWord — Local Speech-to-Text")
        print("=" * 50)
        print(f"  Hotkey  : {self.cfg['hotkey']}")
        print(f"  Mode    : {self.cfg['recording_mode']}")
        print(f"  Model   : {self.cfg['model_size']}")
        print(f"  Device  : {self.cfg['device']}")
        print("=" * 50)

        self.transcriber = Transcriber(
            model_size=self.cfg["model_size"],
            device=self.cfg["device"],
        )

        hotkey_display = self.cfg["hotkey"].replace("+", " + ").title()
        self.tray.start(hotkey_label=hotkey_display)

        if self.cfg.get("show_overlay", True):
            self.overlay = OverlayBar()
            self.overlay.start()

        self._bind_hotkey()

        mode_desc = (
            "HOLD hotkey to record, release to transcribe"
            if self.cfg["recording_mode"] == "hold"
            else "Press hotkey to start, press again to stop"
        )
        print(f"\n[TalkToWord] {mode_desc}")
        print(f"[TalkToWord] Hotkey: {self.cfg['hotkey']}")
        print("[TalkToWord] Running in the system tray.\n")

        keyboard.wait()

    def shutdown(self) -> None:
        print("\n[TalkToWord] Shutting down…")
        self._running = False
        if self.recorder.is_recording:
            self.recorder.stop()
        if self.overlay:
            self.overlay.stop()
        self.tray.stop()
        keyboard.unhook_all()
        os._exit(0)

    # ── hotkey binding ────────────────────────────────────────────────

    def _bind_hotkey(self) -> None:
        keyboard.unhook_all()
        hk = self.cfg["hotkey"]

        if self.cfg["recording_mode"] == "hold":
            keyboard.on_press_key(
                self._last_key(hk),
                self._on_hold_press,
                suppress=True,
            )
            keyboard.on_release_key(
                self._last_key(hk),
                self._on_hold_release,
                suppress=True,
            )
        else:
            keyboard.add_hotkey(hk, self._toggle, suppress=True)

    @staticmethod
    def _last_key(hotkey: str) -> str:
        """Extract the final key from a combo like 'ctrl+shift+space'."""
        return hotkey.split("+")[-1].strip()

    def _modifiers_held(self) -> bool:
        """Check that all modifier keys in the hotkey are currently pressed."""
        parts = [p.strip().lower() for p in self.cfg["hotkey"].split("+")]
        modifiers = parts[:-1]
        for mod in modifiers:
            if mod in ("ctrl", "control") and not keyboard.is_pressed("ctrl"):
                return False
            if mod == "shift" and not keyboard.is_pressed("shift"):
                return False
            if mod == "alt" and not keyboard.is_pressed("alt"):
                return False
            if mod in ("win", "windows", "super") and not keyboard.is_pressed("win"):
                return False
        return True

    # ── hold-to-record mode ──────────────────────────────────────────

    def _on_hold_press(self, event) -> None:
        if self._busy or self._held:
            return
        if not self._modifiers_held():
            return
        self._held = True
        self._start_recording()

    def _on_hold_release(self, event) -> None:
        if not self._held:
            return
        self._held = False
        if self.recorder.is_recording:
            self._stop_and_transcribe()

    # ── toggle mode (press once to start, again to stop) ─────────────

    def _toggle(self) -> None:
        if self._busy:
            return
        if not self.recorder.is_recording:
            self._start_recording()
        else:
            self._stop_and_transcribe()

    # ── shared recording logic ───────────────────────────────────────

    def _start_recording(self) -> None:
        print("[TalkToWord] Recording…")
        self.tray.set_recording()
        if self.overlay:
            self.overlay.set_recording()
        self.recorder.start()

    def _stop_and_transcribe(self) -> None:
        self._busy = True
        wav_data = self.recorder.stop()
        self.tray.set_processing()
        if self.overlay:
            self.overlay.set_processing()
        print("[TalkToWord] Transcribing…")

        thread = threading.Thread(
            target=self._transcribe_and_type,
            args=(wav_data,),
            daemon=True,
        )
        thread.start()

    def _transcribe_and_type(self, wav_data: bytes) -> None:
        try:
            text = self.transcriber.transcribe(wav_data)
            if text:
                print(f'[TalkToWord] "{text}"')
                type_text(text)
            else:
                print("[TalkToWord] (no speech detected)")
        except Exception as e:
            print(f"[TalkToWord] Error: {e}")
        finally:
            self.tray.set_idle()
            if self.overlay:
                self.overlay.set_idle()
            self._busy = False

    # ── settings ─────────────────────────────────────────────────────

    def _open_settings(self) -> None:
        win = SettingsWindow(self.cfg, on_save=self._apply_settings)
        win.open()

    def _apply_settings(self, new_cfg: dict) -> None:
        """Reload config and rebind hotkeys without full restart."""
        print("[TalkToWord] Settings changed, reloading…")
        old_model = self.cfg["model_size"]
        old_device = self.cfg["device"]
        self.cfg = new_cfg

        self._bind_hotkey()

        if new_cfg["model_size"] != old_model or new_cfg["device"] != old_device:
            print("[TalkToWord] Model changed, reloading Whisper…")
            self.transcriber = Transcriber(
                model_size=new_cfg["model_size"],
                device=new_cfg["device"],
            )

        hotkey_display = new_cfg["hotkey"].replace("+", " + ").title()
        self.tray.set_idle()
        mode_desc = (
            "HOLD hotkey to record"
            if new_cfg["recording_mode"] == "hold"
            else "Press hotkey to toggle"
        )
        print(f"[TalkToWord] Reloaded — {mode_desc} ({new_cfg['hotkey']})")

    def _set_mode(self, mode: str) -> None:
        """Quick-switch recording mode from the tray menu."""
        self.cfg["recording_mode"] = mode
        config.save(self.cfg)
        self._bind_hotkey()
        print(f"[TalkToWord] Switched to {mode} mode")
