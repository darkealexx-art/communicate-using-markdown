from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence


class SourceType(str, Enum):
    FILE = "file"
    YOUTUBE = "youtube"


@dataclass(frozen=True)
class IngestItem:
    source_type: SourceType
    source_uri: str
    local_path: Path
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TranscriptSegment:
    text: str
    start_s: float
    end_s: float
    confidence: float
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Transcript:
    segments: Sequence[TranscriptSegment]
    language: str | None
    duration_s: float
    source: IngestItem


class DeltaLabel(str, Enum):
    NOVEDAD_ABSOLUTA = "novedad absoluta"
    MATIZ_REFUERZO = "matiz/refuerzo"
    REDUNDANTE = "redundante"
    RUIDO = "ruido"


@dataclass(frozen=True)
class SimilarityMatch:
    identifier: str
    text: str
    similarity: float
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeltaResult:
    segment: TranscriptSegment
    label: DeltaLabel
    similarity: float
    reason: str
    matches: Sequence[SimilarityMatch] = field(default_factory=tuple)


@dataclass(frozen=True)
class VaultRecord:
    identifier: str
    text: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
