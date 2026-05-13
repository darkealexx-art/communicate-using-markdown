from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Protocol, Sequence

from uhskd.models import SimilarityMatch, VaultRecord


class KnowledgeVaultProtocol(Protocol):
    def upsert(self, records: Sequence[VaultRecord]) -> None:
        ...

    def query_similar(self, text: str, top_k: int = 5) -> Sequence[SimilarityMatch]:
        ...


@dataclass
class InMemoryKnowledgeVault:
    records: dict[str, VaultRecord] = field(default_factory=dict)

    def upsert(self, records: Sequence[VaultRecord]) -> None:
        for record in records:
            self.records[record.identifier] = record

    def query_similar(self, text: str, top_k: int = 5) -> Sequence[SimilarityMatch]:
        candidates: list[SimilarityMatch] = []
        for record in self.records.values():
            similarity = self._jaccard(text, record.text)
            candidates.append(
                SimilarityMatch(
                    identifier=record.identifier,
                    text=record.text,
                    similarity=similarity,
                    metadata=record.metadata,
                )
            )
        candidates.sort(key=lambda match: match.similarity, reverse=True)
        return candidates[:top_k]

    def _jaccard(self, a: str, b: str) -> float:
        tokens_a = self._tokenize(a)
        tokens_b = self._tokenize(b)
        if not tokens_a or not tokens_b:
            return 0.0
        return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)

    def _tokenize(self, text: str) -> set[str]:
        return {token.strip(".,;:!?()[]{}\"").lower() for token in text.split() if token.strip()}
