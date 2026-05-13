from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol, Sequence

from uhskd.models import IngestItem, SourceType


class IngestionSource(Protocol):
    def iter_items(self) -> Iterable[IngestItem]:
        ...


def build_ingest_item(path: Path, source_uri: str | None = None) -> IngestItem:
    return IngestItem(
        source_type=SourceType.FILE,
        source_uri=source_uri or path.as_posix(),
        local_path=path,
        metadata={"filename": path.name},
    )


@dataclass(frozen=True)
class ListIngestionSource:
    items: Sequence[IngestItem]

    def iter_items(self) -> Iterable[IngestItem]:
        yield from self.items
