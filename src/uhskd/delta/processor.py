from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import uuid4

from uhskd.knowledge_vault.base import KnowledgeVault
from uhskd.models import DeltaLabel, DeltaResult, SimilarityMatch, Transcript, TranscriptSegment, VaultRecord


@dataclass(frozen=True)
class DeltaConfig:
    novelty_similarity_threshold: float = 0.3
    reinforcement_similarity_threshold: float = 0.75
    min_characters: int = 20
    min_confidence: float = 0.35
    top_k: int = 5


class DeltaLogicProcessor:
    def __init__(self, vault: KnowledgeVault, config: DeltaConfig | None = None) -> None:
        self._vault = vault
        self._config = config or DeltaConfig()

    def process_transcript(self, transcript: Transcript) -> Sequence[DeltaResult]:
        results: list[DeltaResult] = []
        for segment in transcript.segments:
            results.append(self.classify_segment(segment))
        return results

    def classify_segment(self, segment: TranscriptSegment) -> DeltaResult:
        if len(segment.text.strip()) < self._config.min_characters:
            return self._noise_result(segment, "Segmento demasiado corto")
        if segment.confidence < self._config.min_confidence:
            return self._noise_result(segment, "Baja confianza de transcripción")

        matches = list(self._vault.query_similar(segment.text, top_k=self._config.top_k))
        similarity = max((match.similarity for match in matches), default=0.0)

        if similarity < self._config.novelty_similarity_threshold:
            return DeltaResult(
                segment=segment,
                label=DeltaLabel.NOVEDAD,
                similarity=similarity,
                reason="Contenido nuevo frente al repositorio",
                matches=matches,
            )
        if similarity >= self._config.reinforcement_similarity_threshold:
            return DeltaResult(
                segment=segment,
                label=DeltaLabel.REFUERZO,
                similarity=similarity,
                reason="Refuerza conocimiento existente",
                matches=matches,
            )

        return DeltaResult(
            segment=segment,
            label=DeltaLabel.REFUERZO,
            similarity=similarity,
            reason="Parcialmente alineado con conocimiento existente",
            matches=matches,
        )

    def build_records(self, results: Sequence[DeltaResult]) -> Sequence[VaultRecord]:
        records: list[VaultRecord] = []
        for result in results:
            if result.label is DeltaLabel.RUIDO:
                continue
            records.append(
                VaultRecord(
                    identifier=str(uuid4()),
                    text=result.segment.text,
                    metadata={
                        "label": result.label.value,
                        "start_s": result.segment.start_s,
                        "end_s": result.segment.end_s,
                    },
                )
            )
        return records

    def index_results(self, results: Sequence[DeltaResult]) -> None:
        records = self.build_records(results)
        if records:
            self._vault.upsert(records)

    def _noise_result(self, segment: TranscriptSegment, reason: str) -> DeltaResult:
        return DeltaResult(
            segment=segment,
            label=DeltaLabel.RUIDO,
            similarity=0.0,
            reason=reason,
            matches=(),
        )
