from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from uhskd.models import DeltaResult, Transcript


@dataclass(frozen=True)
class MarkdownOutputGenerator:
    output_dir: Path
    template_path: Path | None = None

    def render_markdown(self, transcript: Transcript, results: Sequence[DeltaResult], title: str) -> str:
        created_at = datetime.now(timezone.utc).isoformat()
        if self.template_path and self.template_path.exists():
            template = self.template_path.read_text(encoding="utf-8")
            content = self._render_segments(results)
            return (
                template.replace("{{ title }}", title)
                .replace("{{ created }}", created_at)
                .replace("{{ source }}", transcript.source.source_uri)
                .replace("{{ content }}", content)
                .strip()
                + "\n"
            )

        lines = [
            "---",
            f"title: {title}",
            f"created: {created_at}",
            f"source: {transcript.source.source_uri}",
            "tags:",
            "  - uhskd",
            "  - delta",
            "---",
            "",
            f"# {title}",
            "",
        ]

        lines.append(self._render_segments(results))

        return "\n".join(lines).strip() + "\n"

    def _render_segments(self, results: Sequence[DeltaResult]) -> str:
        segment_lines: list[str] = []
        for index, result in enumerate(results, start=1):
            label = result.label.value.capitalize()
            timestamp = f"{result.segment.start_s:.2f}s" if result.segment.start_s is not None else ""
            segment_lines.extend(
                [
                    f"## Segmento {index:02d} ({label})",
                    f"- Timestamp: `{timestamp}`",
                    f"- Delta: [[{label}]]",
                    f"- Similaridad: {result.similarity:.2f}",
                    f"- Motivo: {result.reason}",
                    "",
                    result.segment.text,
                    "",
                ]
            )
        return "\n".join(segment_lines).strip()

    def write_markdown(self, transcript: Transcript, results: Sequence[DeltaResult], title: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = self._sanitize_filename(title) + ".md"
        path = self.output_dir / filename
        content = self.render_markdown(transcript, results, title)
        path.write_text(content, encoding="utf-8")
        return path

    def _sanitize_filename(self, title: str) -> str:
        cleaned = "".join(char if char.isalnum() or char in "-_ " else "-" for char in title)
        return "-".join(cleaned.split()).lower()
