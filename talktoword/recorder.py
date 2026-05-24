"""Microphone audio recorder using sounddevice."""

import io
import wave
import threading
import numpy as np
import sounddevice as sd


class AudioRecorder:
    """Records audio from the default microphone into an in-memory WAV buffer."""

    SAMPLE_RATE = 16000  # Whisper expects 16 kHz
    CHANNELS = 1
    DTYPE = "int16"

    def __init__(self):
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self.is_recording = False

    def start(self) -> None:
        with self._lock:
            if self.is_recording:
                return
            self._frames.clear()
            self._stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype=self.DTYPE,
                callback=self._audio_callback,
            )
            self._stream.start()
            self.is_recording = True

    def stop(self) -> bytes:
        """Stop recording and return WAV bytes."""
        with self._lock:
            if not self.is_recording or self._stream is None:
                return b""
            self._stream.stop()
            self._stream.close()
            self._stream = None
            self.is_recording = False
            return self._build_wav()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        self._frames.append(indata.copy())

    def _build_wav(self) -> bytes:
        if not self._frames:
            return b""
        audio = np.concatenate(self._frames, axis=0)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes(audio.tobytes())
        return buf.getvalue()
