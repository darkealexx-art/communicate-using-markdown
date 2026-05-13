from __future__ import annotations

from typing import Protocol

from uhskd.models import IngestItem, Transcript
from uhskd.transcription.faster_whisper import FasterWhisperTranscriber


class Transcriber(Protocol):
    def transcribe(self, item: IngestItem) -> Transcript:
        ...


__all__ = ["FasterWhisperTranscriber", "Transcriber"]
