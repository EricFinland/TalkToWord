"""
Main application — unified hotkey with two behaviors:
  - Hold the hotkey  → record while held, release to transcribe
  - Double-tap       → lock recording on, tap again to stop & transcribe
Popup with pulsing mic animation appears only while recording.
"""

import os
import time
import threading
import keyboard

from talktoword import config
from talktoword.recorder import AudioRecorder
from talktoword.transcriber import Transcriber
from talktoword.typer import type_text
from talktoword.tray import TrayIcon
from talktoword.popup import RecordingPopup
from talktoword.settings_gui import SettingsWindow

DOUBLE_TAP_WINDOW = 0.35  # seconds between taps to count as double-tap
HOLD_THRESHOLD = 0.25     # seconds before a press counts as "holding"


class TalkToWordApp:
    def __init__(self):
        self.cfg = config.load()
        self.recorder = AudioRecorder()
        self.transcriber: Transcriber | None = None
        self.tray = TrayIcon(
            on_quit=self.shutdown,
            on_settings=self._open_settings,
            get_mode=lambda: "both",
            set_mode=lambda m: None,
        )
        self.popup = RecordingPopup()
        self._running = True
        self._busy = False

        # Hotkey state machine
        self._last_press_time = 0.0
        self._pressed = False       # key is physically down right now
        self._held_recording = False # we started recording via hold
        self._locked = False         # recording is locked on (double-tap)
        self._hold_timer: threading.Timer | None = None

    def run(self) -> None:
        print("=" * 50)
        print("  TalkToWord — Local Speech-to-Text")
        print("=" * 50)
        print(f"  Hotkey : {self.cfg['hotkey']}")
        print(f"  Model  : {self.cfg['model_size']}")
        print(f"  Device : {self.cfg['device']}")
        print("=" * 50)

        self.transcriber = Transcriber(
            model_size=self.cfg["model_size"],
            device=self.cfg["device"],
        )

        hotkey_display = self.cfg["hotkey"].replace("+", " + ").title()
        self.tray.start(hotkey_label=hotkey_display)
        self.popup.start()
        self._bind_hotkey()

        print(f"\n[TalkToWord] Hold {self.cfg['hotkey']} to record, release to transcribe.")
        print(f"[TalkToWord] Double-tap {self.cfg['hotkey']} to lock recording on.")
        print("[TalkToWord] Running in the system tray.\n")

        keyboard.wait()

    def shutdown(self) -> None:
        print("\n[TalkToWord] Shutting down…")
        self._running = False
        if self.recorder.is_recording:
            self.recorder.stop()
        self.popup.stop()
        self.tray.stop()
        keyboard.unhook_all()
        os._exit(0)

    # ── hotkey binding ────────────────────────────────────────────────

    def _bind_hotkey(self) -> None:
        keyboard.unhook_all()
        hk = self.cfg["hotkey"]
        last_key = hk.split("+")[-1].strip()

        keyboard.on_press_key(last_key, self._on_key_down, suppress=True)
        keyboard.on_release_key(last_key, self._on_key_up, suppress=True)

    def _modifiers_held(self) -> bool:
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

    # ── key state machine ─────────────────────────────────────────────

    def _on_key_down(self, event) -> None:
        if self._busy or self._pressed:
            return
        if not self._modifiers_held():
            return

        self._pressed = True
        now = time.time()

        # If recording is locked on, a tap stops it
        if self._locked and self.recorder.is_recording:
            self._locked = False
            self._pressed = False
            self._stop_and_transcribe()
            return

        # Check for double-tap
        gap = now - self._last_press_time
        self._last_press_time = now

        if gap < DOUBLE_TAP_WINDOW and not self.recorder.is_recording:
            # Double-tap → lock recording on
            if self._hold_timer:
                self._hold_timer.cancel()
                self._hold_timer = None
            self._locked = True
            self._start_recording(locked=True)
            return

        # Start a timer — if key is still held after threshold, it's a hold
        self._hold_timer = threading.Timer(HOLD_THRESHOLD, self._hold_triggered)
        self._hold_timer.daemon = True
        self._hold_timer.start()

    def _hold_triggered(self) -> None:
        """Called when key has been held past the threshold."""
        if self._pressed and not self._locked and not self.recorder.is_recording:
            self._held_recording = True
            self._start_recording(locked=False)

    def _on_key_up(self, event) -> None:
        self._pressed = False

        # Cancel hold timer if released quickly (it was a tap, not a hold)
        if self._hold_timer:
            self._hold_timer.cancel()
            self._hold_timer = None

        # If we were hold-recording, stop on release
        if self._held_recording and self.recorder.is_recording:
            self._held_recording = False
            self._stop_and_transcribe()

        # If locked, release does nothing — recording continues

    # ── recording ─────────────────────────────────────────────────────

    def _start_recording(self, locked: bool) -> None:
        print(f"[TalkToWord] Recording… ({'locked' if locked else 'hold'})")
        self.tray.set_recording()
        self.popup.show_recording(locked=locked)
        self.recorder.start()

    def _stop_and_transcribe(self) -> None:
        self._busy = True
        self._held_recording = False
        self._locked = False
        wav_data = self.recorder.stop()
        self.tray.set_processing()
        self.popup.show_processing()
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
                self.popup.hide()
                time.sleep(0.05)
                type_text(text)
            else:
                print("[TalkToWord] (no speech detected)")
                self.popup.hide()
        except Exception as e:
            print(f"[TalkToWord] Error: {e}")
            self.popup.hide()
        finally:
            self.tray.set_idle()
            self._busy = False

    # ── settings ─────────────────────────────────────────────────────

    def _open_settings(self) -> None:
        win = SettingsWindow(self.cfg, on_save=self._apply_settings)
        win.open()

    def _apply_settings(self, new_cfg: dict) -> None:
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

        self.tray.set_idle()
        print(f"[TalkToWord] Reloaded ({new_cfg['hotkey']})")
