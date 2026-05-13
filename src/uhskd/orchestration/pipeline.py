from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from uhskd.delta.processor import DeltaProcessor
from uhskd.ingestion.base import IngestionSource
from uhskd.models import DeltaResult, IngestItem, Transcript
from uhskd.output.markdown import MarkdownOutputGenerator
from uhskd.transcription import Transcriber


@dataclass(frozen=True)
class PipelineResult:
    item: IngestItem
    transcript: Transcript
    delta_results: Sequence[DeltaResult]
    output_path: Path | None


class Pipeline:
    def __init__(
        self,
        transcriber: Transcriber,
        delta_processor: DeltaProcessor,
        output_generator: MarkdownOutputGenerator | None = None,
    ) -> None:
        self._transcriber = transcriber
        self._delta_processor = delta_processor
        self._output_generator = output_generator

    def run_item(self, item: IngestItem, title: str | None = None, index_results: bool = True) -> PipelineResult:
        transcript = self._transcriber.transcribe(item)
        results = self._delta_processor.process_transcript(transcript)
        if index_results:
            self._delta_processor.index_results(results)

        output_path = None
        if self._output_generator:
            output_title = title or item.metadata.get("title") or item.local_path.stem
            output_path = self._output_generator.write_markdown(transcript, results, str(output_title))

        return PipelineResult(
            item=item,
            transcript=transcript,
            delta_results=results,
            output_path=output_path,
        )

    def run_source(self, source: IngestionSource, index_results: bool = True) -> Iterable[PipelineResult]:
        for item in source.iter_items():
            yield self.run_item(item, index_results=index_results)
