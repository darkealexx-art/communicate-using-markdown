from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence
from uuid import uuid4

from uhskd.knowledge_vault.base import KnowledgeVaultProtocol
from uhskd.models import DeltaLabel, DeltaResult, SimilarityMatch, Transcript, TranscriptSegment, VaultRecord


@dataclass(frozen=True)
class DeltaConfig:
    novelty_similarity_threshold: float = 0.3
    reinforcement_similarity_threshold: float = 0.7
    min_characters: int = 20
    min_confidence: float = 0.35
    top_k: int = 5
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    summary_template: str = (
        "## Delta Summary\n"
        "- Segmento: {segment}\n"
        "- Clasificación: {label}\n"
        "- Score máximo: {score:.2f}\n"
        "- Motivo: {reason}\n"
        "- Coincidencias:\n{matches}\n"
    )


class DeltaProcessor:
    def __init__(
        self,
        vault: KnowledgeVaultProtocol,
        config: DeltaConfig | None = None,
        cross_encoder: Any | None = None,
    ) -> None:
        self._vault = vault
        self._config = config or DeltaConfig()
        if cross_encoder is None:
            try:
                from sentence_transformers import CrossEncoder
            except ModuleNotFoundError as exc:
                raise RuntimeError("sentence-transformers is required for DeltaProcessor") from exc
            cross_encoder = CrossEncoder(self._config.cross_encoder_model)
        self._cross_encoder = cross_encoder

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

        retrieved = list(self._retrieve_matches(segment.text))
        matches = list(self.rerank_documents(segment.text, retrieved))
        similarity = max((match.similarity for match in matches), default=0.0)

        if similarity < self._config.novelty_similarity_threshold:
            return DeltaResult(
                segment=segment,
                label=DeltaLabel.NOVEDAD_ABSOLUTA,
                similarity=similarity,
                reason="Contenido nuevo frente al repositorio",
                matches=matches,
            )
        if similarity >= self._config.reinforcement_similarity_threshold:
            return DeltaResult(
                segment=segment,
                label=DeltaLabel.REDUNDANTE,
                similarity=similarity,
                reason="Contenido redundante con el repositorio",
                matches=matches,
            )

        return DeltaResult(
            segment=segment,
            label=DeltaLabel.MATIZ_REFUERZO,
            similarity=similarity,
            reason="Complementa o refuerza conocimiento existente",
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

    def rerank_documents(
        self, query_text: str, retrieved_documents: Sequence[SimilarityMatch]
    ) -> Sequence[SimilarityMatch]:
        if not retrieved_documents:
            return ()
        pairs = [(query_text, doc.text) for doc in retrieved_documents]
        scores = self._cross_encoder.predict(pairs)
        reranked = [
            SimilarityMatch(
                identifier=doc.identifier,
                text=doc.text,
                similarity=float(score),
                metadata=doc.metadata,
            )
            for doc, score in zip(retrieved_documents, scores, strict=True)
        ]
        reranked.sort(key=lambda match: match.similarity, reverse=True)
        return reranked

    def generate_delta_summary(self, result: DeltaResult, template: str | None = None) -> str:
        template_text = template or self._config.summary_template
        matches_text = "\n".join(
            f"- ({match.similarity:.2f}) {match.text}" for match in result.matches
        ) or "- (sin coincidencias)"
        return template_text.format(
            segment=result.segment.text,
            label=result.label.value,
            score=result.similarity,
            reason=result.reason,
            matches=matches_text,
        ).strip()

    def _retrieve_matches(self, text: str) -> Iterable[SimilarityMatch]:
        if hasattr(self._vault, "query_knowledge"):
            return self._vault.query_knowledge(text, n_results=self._config.top_k)
        return self._vault.query_similar(text, top_k=self._config.top_k)

    def _noise_result(self, segment: TranscriptSegment, reason: str) -> DeltaResult:
        return DeltaResult(
            segment=segment,
            label=DeltaLabel.RUIDO,
            similarity=0.0,
            reason=reason,
            matches=(),
        )


class DeltaLogicProcessor(DeltaProcessor):
    """Backward-compatible alias for integrations that still import DeltaLogicProcessor."""
