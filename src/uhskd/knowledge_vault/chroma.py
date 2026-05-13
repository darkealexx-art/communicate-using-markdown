from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

from uhskd.knowledge_vault.base import KnowledgeVaultProtocol
from uhskd.models import SimilarityMatch, VaultRecord


@dataclass
class ChromaKnowledgeVault(KnowledgeVaultProtocol):
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


@dataclass
class KnowledgeVault:
    persist_dir: Path
    collection_name: str = "uhskd"
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 50
    model_name: str = "all-MiniLM-L6-v2"
    _model: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.chunk_overlap_tokens >= self.chunk_size_tokens:
            raise ValueError("chunk_overlap_tokens must be smaller than chunk_size_tokens")

        try:
            import chromadb
        except ModuleNotFoundError as exc:
            raise RuntimeError("chromadb is required for the knowledge vault") from exc

        try:
            from sentence_transformers import SentenceTransformer
        except ModuleNotFoundError as exc:
            raise RuntimeError("sentence-transformers is required for embeddings") from exc

        self._model = SentenceTransformer(self.model_name)
        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = self._client.get_or_create_collection(self.collection_name)

    def add_knowledge(self, text: str, metadata: dict[str, Any] | None = None) -> Sequence[str]:
        chunks = self._chunk_text(text)
        if not chunks:
            return ()

        embeddings = self._model.encode(chunks, convert_to_numpy=True).tolist()
        base_id = str(uuid4())
        ids = [f"{base_id}-{index}" for index in range(len(chunks))]
        metadatas = [self._build_metadata(metadata, index) for index in range(len(chunks))]

        self._collection.upsert(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
        return ids

    def query_knowledge(self, text: str, top_k: int = 5) -> Sequence[SimilarityMatch]:
        embedding = self._model.encode([text], convert_to_numpy=True).tolist()
        results = self._collection.query(query_embeddings=embedding, n_results=top_k)
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

    def _chunk_text(self, text: str) -> list[str]:
        tokenizer = self._model.tokenizer
        tokens = tokenizer.encode(text, add_special_tokens=False)
        if not tokens:
            return []
        step = max(1, self.chunk_size_tokens - self.chunk_overlap_tokens)

        chunks: list[str] = []
        for start in range(0, len(tokens), step):
            end = min(start + self.chunk_size_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            if not chunk_tokens:
                continue
            chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True).strip()
            if chunk_text:
                chunks.append(chunk_text)
            if end >= len(tokens):
                break
        return chunks

    def _build_metadata(self, metadata: dict[str, Any] | None, chunk_index: int) -> dict[str, Any]:
        payload = dict(metadata or {})
        payload["chunk_index"] = chunk_index
        return payload
