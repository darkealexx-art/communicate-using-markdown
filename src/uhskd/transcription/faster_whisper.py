from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

from uhskd.models import IngestItem, Transcript, TranscriptSegment


@dataclass(frozen=True)
class FasterWhisperTranscriber:
    model_size: str = "base"
    device: str = "cpu"
    compute_type: str = "int8"
    beam_size: int = 5
    vad_filter: bool = True

    def transcribe(self, item: IngestItem) -> Transcript:
        try:
            from faster_whisper import WhisperModel
        except ModuleNotFoundError as exc:
            raise RuntimeError("faster-whisper is required for transcription") from exc

        model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        segments, info = model.transcribe(
            str(item.local_path),
            beam_size=self.beam_size,
            vad_filter=self.vad_filter,
        )

        transcript_segments = [self._to_segment(segment, item) for segment in segments]
        duration_s = float(info.duration) if getattr(info, "duration", None) else 0.0

        return Transcript(
            segments=transcript_segments,
            language=getattr(info, "language", None),
            duration_s=duration_s,
            source=item,
        )

    def _to_segment(self, segment: object, item: IngestItem) -> TranscriptSegment:
        start = float(getattr(segment, "start", 0.0))
        end = float(getattr(segment, "end", 0.0))
        text = str(getattr(segment, "text", "")).strip()
        avg_logprob = getattr(segment, "avg_logprob", None)
        confidence = self._logprob_to_confidence(avg_logprob)

        return TranscriptSegment(
            text=text,
            start_s=start,
            end_s=end,
            confidence=confidence,
            metadata={"source_uri": item.source_uri},
        )

    def _logprob_to_confidence(self, avg_logprob: float | None) -> float:
        if avg_logprob is None:
            return 0.0
        return 1 / (1 + math.exp(-float(avg_logprob)))
