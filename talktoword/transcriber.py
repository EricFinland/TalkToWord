"""Local speech-to-text using faster-whisper (CTranslate2 Whisper)."""

import io
import sys
import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    """Wraps faster-whisper for local, offline transcription."""

    def __init__(self, model_size: str = "base", device: str = "auto"):
        """
        Args:
            model_size: Whisper model to load. Options:
                        tiny, base, small, medium, large-v3
                        Larger = more accurate but slower.
            device:     "auto" picks CUDA if available, else CPU.
        """
        compute_type = "int8"
        if device == "auto":
            device = "cuda" if self._cuda_available() else "cpu"

        print(f"[TalkToWord] Loading Whisper '{model_size}' on {device}…")
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )
        print("[TalkToWord] Model loaded.")

    def transcribe(self, wav_bytes: bytes) -> str:
        """Transcribe WAV audio bytes to text."""
        if not wav_bytes:
            return ""

        audio = self._wav_bytes_to_float32(wav_bytes)
        segments, _info = self.model.transcribe(
            audio,
            beam_size=5,
            language="en",
            vad_filter=True,
        )
        return " ".join(seg.text.strip() for seg in segments).strip()

    @staticmethod
    def _wav_bytes_to_float32(wav_bytes: bytes) -> np.ndarray:
        """Convert 16-bit PCM WAV bytes to float32 numpy array."""
        import wave

        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        pcm = np.frombuffer(raw, dtype=np.int16)
        return pcm.astype(np.float32) / 32768.0

    @staticmethod
    def _cuda_available() -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
