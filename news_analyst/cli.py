"""Command line interface for news_analyst."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

from news_analyst.analysis import analyze_segment
from news_analyst.config import AppConfig, load_config
from news_analyst.http import create_http_session
from news_analyst.processing import deduplicate_items, enrich_items, filter_by_relevance, sort_items
from news_analyst.report import build_report
from news_analyst.sources import fetch_items
from news_analyst.utils import ensure_parent_dir


def setup_logging(config: AppConfig) -> logging.Logger:
    logger = logging.getLogger("news_analyst")
    level = getattr(logging, config.logging.level.upper(), logging.INFO)
    logger.setLevel(level)
    logger.handlers.clear()

    log_path = ensure_parent_dir(config.logging.file)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def run(config_path: str) -> str:
    config = load_config(config_path)
    logger = setup_logging(config)
    session = create_http_session()
    analyses = []

    logger.info("Inicio de recopilación de noticias.")
    for segment in config.segments.values():
        if not segment.enabled:
            logger.info("Segmento deshabilitado: %s", segment.display_name)
            continue

        segment_items = []
        for source in segment.sources:
            try:
                fetched = fetch_items(
                    source,
                    session,
                    config.report.max_items_per_segment,
                    segment.display_name,
                    source.language or config.report.language,
                    logger,
                )
                segment_items.extend(enrich_items(fetched))
            except Exception as exc:
                logger.exception(
                    "Fallo al consultar fuente %s (%s): %s",
                    source.name,
                    source.url,
                    exc,
                )

        filtered = filter_by_relevance(
            segment_items, config.filters.min_relevance_score
        )
        deduped = deduplicate_items(
            filtered, config.filters.deduplication_similarity_threshold
        )
        sorted_items = sort_items(deduped)[: config.report.max_items_per_segment]

        analyses.append(
            analyze_segment(segment.key, segment.display_name, sorted_items)
        )
        logger.info(
            "Segmento %s: %s noticias seleccionadas.",
            segment.display_name,
            len(sorted_items),
        )

    report_path = build_report(config.report, analyses)
    logger.info("Reporte generado en %s", report_path)
    logger.info("Finalizado en %s", datetime.now(timezone.utc).isoformat())
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analista automatizado de noticias."
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Ruta al archivo config.yaml",
    )
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()
