from datetime import datetime, timezone
from pathlib import Path

from news_analyst.analysis import SegmentAnalysis
from news_analyst.config import ReportConfig
from news_analyst.models import NewsItem
from news_analyst.report import build_report


def test_report_generation(tmp_path: Path) -> None:
    report = ReportConfig(
        title="Informe de prueba",
        language="es",
        period="daily",
        date_range_days=1,
        max_items_per_segment=3,
        output_path=str(tmp_path / "reporte.docx"),
    )
    item = NewsItem(
        title="Avance tecnológico relevante",
        source="Fuente Tech",
        url="https://example.com/tech",
        published_at=datetime.now(timezone.utc),
        author="Editor",
        summary="Resumen corto",
        content="Contenido",
        segment="Noticias de tecnología",
        language="es",
        consulted_at=datetime.now(timezone.utc),
        relevance_score=4,
        relevance_reason="Palabras clave detectadas.",
        source_type="medio especializado",
        impact_level="alto",
    )
    analysis = SegmentAnalysis(
        segment_key="technology",
        segment_display_name="Noticias de tecnología",
        executive_summary="Resumen ejecutivo",
        deep_analysis="Análisis profundo",
        trends=["inteligencia"],
        risks=["Riesgo potencial"],
        opportunities=["Oportunidad emergente"],
        implications=["Implicación"],
        items=[item],
    )

    output_path = build_report(report, [analysis])
    assert Path(output_path).exists()
    assert Path(output_path).stat().st_size > 0
