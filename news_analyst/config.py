"""Configuration loading for news_analyst."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml


@dataclass
class ReportConfig:
    title: str
    language: str
    period: str
    date_range_days: int
    max_items_per_segment: int
    output_path: str


@dataclass
class FiltersConfig:
    min_relevance_score: int
    deduplication_similarity_threshold: float


@dataclass
class LoggingConfig:
    level: str
    file: str


@dataclass
class SourceConfig:
    name: str
    type: str
    url: str
    source_type: str
    language: Optional[str] = None


@dataclass
class SegmentConfig:
    key: str
    display_name: str
    enabled: bool
    sources: List[SourceConfig]


@dataclass
class AppConfig:
    report: ReportConfig
    filters: FiltersConfig
    logging: LoggingConfig
    segments: Dict[str, SegmentConfig]


def load_config(path: str) -> AppConfig:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    report_data = data.get("report", {})
    report = ReportConfig(
        title=report_data.get("title", "Informe Ejecutivo de Noticias"),
        language=report_data.get("language", "es"),
        period=report_data.get("period", "daily"),
        date_range_days=int(report_data.get("date_range_days", 1)),
        max_items_per_segment=int(report_data.get("max_items_per_segment", 10)),
        output_path=report_data.get("output_path", "output/informe_noticias.docx"),
    )

    filters_data = data.get("filters", {})
    filters = FiltersConfig(
        min_relevance_score=int(filters_data.get("min_relevance_score", 3)),
        deduplication_similarity_threshold=float(
            filters_data.get("deduplication_similarity_threshold", 0.82)
        ),
    )

    logging_data = data.get("logging", {})
    logging_cfg = LoggingConfig(
        level=logging_data.get("level", "INFO"),
        file=logging_data.get("file", "logs/news_analyst.log"),
    )

    segments: Dict[str, SegmentConfig] = {}
    for key, segment_data in (data.get("segments") or {}).items():
        sources = [
            SourceConfig(
                name=source.get("name", "Fuente sin nombre"),
                type=source.get("type", "rss"),
                url=source.get("url", ""),
                source_type=source.get("source_type", ""),
                language=source.get("language"),
            )
            for source in (segment_data.get("sources") or [])
        ]
        segments[key] = SegmentConfig(
            key=key,
            display_name=segment_data.get("display_name", key),
            enabled=bool(segment_data.get("enabled", True)),
            sources=sources,
        )

    if not segments:
        raise ValueError(
            f"El archivo {path} debe incluir segmentos configurados."
        )

    return AppConfig(
        report=report,
        filters=filters,
        logging=logging_cfg,
        segments=segments,
    )
