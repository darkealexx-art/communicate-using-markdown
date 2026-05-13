from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from uhskd.knowledge_vault.base import KnowledgeVault
from uhskd.models import SimilarityMatch, VaultRecord


@dataclass
class ChromaKnowledgeVault(KnowledgeVault):
    persist_dir: Path
    collection_name: str = "uhskd"

    def __post_init__(self) -> None:
        try:
            import chromadb
        except ModuleNotFoundError as exc:
            raise RuntimeError("chromadb is required for the knowledge vault") from exc

        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = self._client.get_or_create_collection(self.collection_name)

    def upsert(self, records: Sequence[VaultRecord]) -> None:
        if not records:
            return
        self._collection.upsert(
            ids=[record.identifier for record in records],
            documents=[record.text for record in records],
            metadatas=[record.metadata for record in records],
        )

    def query_similar(self, text: str, top_k: int = 5) -> Sequence[SimilarityMatch]:
        results = self._collection.query(query_texts=[text], n_results=top_k)
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        matches: list[SimilarityMatch] = []
        for identifier, document, metadata, distance in zip(ids, documents, metadatas, distances, strict=True):
            similarity = 1.0 - float(distance) if distance is not None else 0.0
            matches.append(
                SimilarityMatch(
                    identifier=str(identifier),
                    text=str(document),
                    similarity=similarity,
                    metadata=metadata or {},
                )
            )
        return matches
