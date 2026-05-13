from datetime import datetime, timezone

from news_analyst.models import NewsItem
from news_analyst.processing import deduplicate_items, enrich_items


def _make_item(title: str, source: str) -> NewsItem:
    return NewsItem(
        title=title,
        source=source,
        url=f"https://example.com/{source}",
        published_at=datetime.now(timezone.utc),
        author=None,
        summary="Resumen breve",
        content="Contenido de respaldo",
        segment="Noticias de México",
        language="es",
        consulted_at=datetime.now(timezone.utc),
        relevance_score=0,
        relevance_reason="",
        source_type="medio nacional",
        impact_level="pendiente",
    )


def test_relevance_scoring_keywords() -> None:
    items = enrich_items([_make_item("Crisis económica en la región", "Fuente A")])
    assert items[0].relevance_score >= 4


def test_deduplication_merges_sources() -> None:
    item_a = _make_item("Reforma fiscal en México", "Fuente A")
    item_b = _make_item("Reforma fiscal en Mexico", "Fuente B")
    enriched = enrich_items([item_a, item_b])
    deduped = deduplicate_items(enriched, threshold=0.8)
    assert len(deduped) == 1
    assert "Fuente B" in deduped[0].related_sources
