"""JSON source ingestion."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import requests

from news_analyst.config import SourceConfig
from news_analyst.models import NewsItem
from news_analyst.utils import parse_datetime, strip_html


def _load_json(source: SourceConfig, session: requests.Session) -> object:
    if source.url.startswith("http://") or source.url.startswith("https://"):
        response = session.get(source.url, timeout=10)
        response.raise_for_status()
        return response.json()
    return json.loads(Path(source.url).read_text(encoding="utf-8"))


def fetch_json_items(
    source: SourceConfig,
    session: requests.Session,
    max_items: int,
    segment: str,
    language: str,
    logger,
) -> List[NewsItem]:
    if not source.url:
        logger.warning("Fuente JSON sin URL configurada: %s", source.name)
        return []

    payload = _load_json(source, session)
    if isinstance(payload, dict):
        entries = payload.get("items") or payload.get("articles") or payload.get("data") or []
    elif isinstance(payload, list):
        entries = payload
    else:
        logger.warning("Formato JSON no reconocido para %s", source.name)
        return []

    consulted_at = datetime.now(timezone.utc)
    items: List[NewsItem] = []
    for entry in entries[:max_items]:
        if not isinstance(entry, dict):
            continue
        title = strip_html(entry.get("title") or "")
        link = entry.get("url") or entry.get("link")
        if not title or not link:
            continue
        summary = strip_html(entry.get("summary") or entry.get("description") or "")
        content = strip_html(entry.get("content") or "")
        published_at = parse_datetime(
            entry.get("published_at")
            or entry.get("published")
            or entry.get("updated_at")
            or entry.get("date")
        )
        items.append(
            NewsItem(
                title=title,
                source=entry.get("source") or source.name,
                url=link,
                published_at=published_at,
                author=entry.get("author"),
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
