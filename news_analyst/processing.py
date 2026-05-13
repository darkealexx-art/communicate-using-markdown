"""Processing utilities: scoring, deduplication, and filtering."""

from __future__ import annotations

from dataclasses import replace
from difflib import SequenceMatcher
from typing import Iterable, List

from news_analyst.models import NewsItem
from news_analyst.utils import normalize_text

KEYWORD_WEIGHTS = {
    "crisis": 1,
    "urgente": 1,
    "emergencia": 1,
    "alerta": 1,
    "presidente": 1,
    "congreso": 1,
    "reforma": 1,
    "inversion": 1,
    "crecimiento": 1,
    "inflacion": 1,
    "conflicto": 1,
    "ciberseguridad": 1,
    "inteligencia artificial": 1,
    "descubrimiento": 1,
    "vacuna": 1,
    "regulacion": 1,
    "pandemia": 1,
}


def score_relevance(item: NewsItem) -> tuple[int, str]:
    text = normalize_text(f"{item.title} {item.summary} {item.content}")
    score = 3
    matches: list[str] = []
    for keyword, weight in KEYWORD_WEIGHTS.items():
        if keyword in text:
            score += weight
            matches.append(keyword)
    score = max(1, min(5, score))
    if matches:
        reason = f"Palabras clave detectadas: {', '.join(sorted(set(matches)))}."
    else:
        reason = "Sin señales de alto impacto; relevancia moderada por defecto."
    return score, reason


def impact_level_from_score(score: int) -> str:
    if score >= 5:
        return "crítico"
    if score == 4:
        return "alto"
    if score == 3:
        return "medio"
    return "bajo"


def enrich_items(items: Iterable[NewsItem]) -> List[NewsItem]:
    enriched: List[NewsItem] = []
    for item in items:
        score, reason = score_relevance(item)
        enriched.append(
            replace(
                item,
                relevance_score=score,
                relevance_reason=reason,
                impact_level=impact_level_from_score(score),
            )
        )
    return enriched


def filter_by_relevance(items: Iterable[NewsItem], min_score: int) -> List[NewsItem]:
    return [item for item in items if item.relevance_score >= min_score]


def similarity(a: NewsItem, b: NewsItem) -> float:
    text_a = normalize_text(f"{a.title} {a.summary}")
    text_b = normalize_text(f"{b.title} {b.summary}")
    if not text_a or not text_b:
        return 0.0
    return SequenceMatcher(None, text_a, text_b).ratio()


def deduplicate_items(items: Iterable[NewsItem], threshold: float) -> List[NewsItem]:
    unique: List[NewsItem] = []
    for item in items:
        duplicate_found = False
        for idx, existing in enumerate(unique):
            if similarity(existing, item) >= threshold:
                duplicate_found = True
                related_sources = set(existing.related_sources)
                if item.source != existing.source:
                    related_sources.add(item.source)
                updated = existing
                if item.relevance_score > existing.relevance_score:
                    updated = replace(
                        existing,
                        relevance_score=item.relevance_score,
                        relevance_reason=item.relevance_reason,
                        impact_level=item.impact_level,
                    )
                if item.published_at and (
                    not updated.published_at or item.published_at > updated.published_at
                ):
                    updated = replace(updated, published_at=item.published_at, url=item.url)
                unique[idx] = replace(updated, related_sources=sorted(related_sources))
                break
        if not duplicate_found:
            unique.append(item)
    return unique


def sort_items(items: Iterable[NewsItem]) -> List[NewsItem]:
    return sorted(
        items,
        key=lambda item: (
            item.relevance_score,
            item.published_at or item.consulted_at,
        ),
        reverse=True,
    )
