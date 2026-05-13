"""RSS source ingestion."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import feedparser
import requests

from news_analyst.config import SourceConfig
from news_analyst.models import NewsItem
from news_analyst.utils import parse_datetime, strip_html


def fetch_rss_items(
    source: SourceConfig,
    session: requests.Session,
    max_items: int,
    segment: str,
    language: str,
    logger,
) -> List[NewsItem]:
    if not source.url:
        logger.warning("Fuente RSS sin URL configurada: %s", source.name)
        return []

    response = session.get(source.url, timeout=10)
    response.raise_for_status()
    feed = feedparser.parse(response.content)

    consulted_at = datetime.now(timezone.utc)
    items: List[NewsItem] = []
    for entry in feed.entries[:max_items]:
        title = strip_html(entry.get("title"))
        link = entry.get("link")
        if not title or not link:
            continue
        summary = strip_html(entry.get("summary") or entry.get("description"))
        content = ""
        if entry.get("content"):
            content = strip_html(entry.get("content")[0].get("value", ""))
        published_at = parse_datetime(entry.get("published") or entry.get("updated"))
        items.append(
            NewsItem(
                title=title,
                source=source.name,
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
