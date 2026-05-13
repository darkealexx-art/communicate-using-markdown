from pathlib import Path

from uhskd.models import DeltaLabel, DeltaResult, IngestItem, SourceType, Transcript, TranscriptSegment
from uhskd.output.markdown import MarkdownOutputGenerator


def test_markdown_output_includes_frontmatter(tmp_path: Path) -> None:
    generator = MarkdownOutputGenerator(output_dir=tmp_path)
    item = IngestItem(
        source_type=SourceType.FILE,
        source_uri="file:///demo.wav",
        local_path=Path("demo.wav"),
        metadata={},
    )
    transcript = Transcript(
        segments=[TranscriptSegment(text="contenido", start_s=0.0, end_s=1.0, confidence=0.8)],
        language="es",
        duration_s=1.0,
        source=item,
    )
    results = [
        DeltaResult(
            segment=transcript.segments[0],
            label=DeltaLabel.NOVEDAD_ABSOLUTA,
            similarity=0.1,
            reason="nuevo",
            matches=(),
        )
    ]

    content = generator.render_markdown(transcript, results, "Demo")

    assert content.startswith("---")
    assert "title: Demo" in content
    assert "source: file:///demo.wav" in content
