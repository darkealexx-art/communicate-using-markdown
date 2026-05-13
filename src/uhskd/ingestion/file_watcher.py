from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import time
from typing import Iterable, Sequence

from uhskd.ingestion.base import IngestionSource, build_ingest_item
from uhskd.models import IngestItem


@dataclass(frozen=True)
class FileIngestionSource:
    paths: Sequence[Path]

    def iter_items(self) -> Iterable[IngestItem]:
        for path in self.paths:
            if path.exists() and path.is_file():
                yield build_ingest_item(path)


@dataclass
class FolderWatcher:
    watch_path: Path
    extensions: Sequence[str] = field(default_factory=lambda: (".mp3", ".wav", ".m4a", ".mp4", ".mkv"))
    poll_interval_s: float = 2.0
    recursive: bool = True

    def iter_items(self) -> Iterable[IngestItem]:
        self.watch_path.mkdir(parents=True, exist_ok=True)

        try:
            from watchfiles import watch
        except ModuleNotFoundError:
            yield from self._poll_for_items()
            return

        for changes in watch(self.watch_path, recursive=self.recursive):
            for _, file_path in changes:
                path = Path(file_path)
                if self._is_valid(path):
                    yield build_ingest_item(path)

    def _poll_for_items(self) -> Iterable[IngestItem]:
        seen: set[Path] = set()
        while True:
            for path in self._iter_paths():
                if path not in seen and self._is_valid(path):
                    seen.add(path)
                    yield build_ingest_item(path)
            time.sleep(self.poll_interval_s)

    def _iter_paths(self) -> Iterable[Path]:
        if self.recursive:
            yield from self.watch_path.rglob("*")
        else:
            yield from self.watch_path.glob("*")

    def _is_valid(self, path: Path) -> bool:
        return path.is_file() and path.suffix.lower() in {ext.lower() for ext in self.extensions}
