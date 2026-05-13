"""Source dispatchers for news ingestion."""

from __future__ import annotations

from typing import List

import requests

from news_analyst.config import SourceConfig
from news_analyst.models import NewsItem
from news_analyst.sources.csv_source import fetch_csv_items
from news_analyst.sources.json_source import fetch_json_items
from news_analyst.sources.rss import fetch_rss_items


def fetch_items(
    source: SourceConfig,
    session: requests.Session,
    max_items: int,
    segment: str,
    language: str,
    logger,
) -> List[NewsItem]:
    source_type = source.type.lower()
    if source_type == "rss":
        return fetch_rss_items(source, session, max_items, segment, language, logger)
    if source_type == "json":
        return fetch_json_items(source, session, max_items, segment, language, logger)
    if source_type == "csv":
        return fetch_csv_items(source, session, max_items, segment, language, logger)
    logger.warning("Tipo de fuente no soportado: %s", source.type)
    return []
