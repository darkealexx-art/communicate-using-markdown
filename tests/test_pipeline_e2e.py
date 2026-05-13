from pathlib import Path

from uhskd.delta.processor import DeltaLogicProcessor
from uhskd.knowledge_vault.base import InMemoryKnowledgeVault
from uhskd.models import IngestItem, SourceType, Transcript, TranscriptSegment
from uhskd.orchestration.pipeline import Pipeline
from uhskd.output.markdown import MarkdownOutputGenerator


class StubTranscriber:
    def transcribe(self, item: IngestItem) -> Transcript:
        return Transcript(
            segments=[
                TranscriptSegment(
                    text="insight relevante para el repositorio",
                    start_s=0.0,
                    end_s=2.0,
                    confidence=0.9,
                )
            ],
            language="es",
            duration_s=2.0,
            source=item,
        )


def test_pipeline_end_to_end(tmp_path: Path) -> None:
    vault = InMemoryKnowledgeVault()
    delta = DeltaLogicProcessor(vault)
    output = MarkdownOutputGenerator(output_dir=tmp_path)
    pipeline = Pipeline(transcriber=StubTranscriber(), delta_processor=delta, output_generator=output)

    item = IngestItem(
        source_type=SourceType.FILE,
        source_uri="file:///sample.wav",
        local_path=Path("sample.wav"),
        metadata={},
    )

    result = pipeline.run_item(item)

    assert result.output_path is not None
    assert result.output_path.exists()
    assert len(result.delta_results) == 1
