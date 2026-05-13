"""CSV source ingestion."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import requests

from news_analyst.config import SourceConfig
from news_analyst.models import NewsItem
from news_analyst.utils import parse_datetime, strip_html


def _load_csv_rows(source: SourceConfig, session: requests.Session) -> list[dict]:
    if source.url.startswith("http://") or source.url.startswith("https://"):
        response = session.get(source.url, timeout=10)
        response.raise_for_status()
        content = response.text
    else:
        content = Path(source.url).read_text(encoding="utf-8")
    reader = csv.DictReader(content.splitlines())
    return list(reader)


def fetch_csv_items(
    source: SourceConfig,
    session: requests.Session,
    max_items: int,
    segment: str,
    language: str,
    logger,
) -> List[NewsItem]:
    if not source.url:
        logger.warning("Fuente CSV sin URL configurada: %s", source.name)
        return []

    rows = _load_csv_rows(source, session)
    consulted_at = datetime.now(timezone.utc)
    items: List[NewsItem] = []
    for row in rows[:max_items]:
        title = strip_html(row.get("title") or "")
        link = row.get("url") or row.get("link")
        if not title or not link:
            continue
        summary = strip_html(row.get("summary") or row.get("description") or "")
        content = strip_html(row.get("content") or "")
        published_at = parse_datetime(
            row.get("published_at") or row.get("published") or row.get("date")
        )
        items.append(
            NewsItem(
                title=title,
                source=row.get("source") or source.name,
                url=link,
                published_at=published_at,
                author=row.get("author"),
                summary=summary,
                content=content,
                segment=segment,
                language=language,
                consulted_at=consulted_at,
                relevance_score=0,
                relevance_reason="",
                source_type=source.source_type,
                impact_level="pendiente",
            )
        )
    return items
