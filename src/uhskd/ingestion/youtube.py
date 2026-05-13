from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from uhskd.models import IngestItem, SourceType


@dataclass(frozen=True)
class YouTubeIngestionSource:
    urls: Sequence[str]
    download_dir: Path

    def iter_items(self) -> Iterable[IngestItem]:
        self.download_dir.mkdir(parents=True, exist_ok=True)

        try:
            import yt_dlp
        except ModuleNotFoundError as exc:
            raise RuntimeError("yt-dlp is required for YouTube ingestion") from exc

        ydl_opts = {
            "outtmpl": str(self.download_dir / "%(id)s.%(ext)s"),
            "format": "bestaudio/best",
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in self.urls:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                path = Path(filename)
                yield IngestItem(
                    source_type=SourceType.YOUTUBE,
                    source_uri=url,
                    local_path=path,
                    metadata={
                        "title": info.get("title"),
                        "uploader": info.get("uploader"),
                        "duration": info.get("duration"),
                    },
                )
