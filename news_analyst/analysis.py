"""Analytical summaries for news segments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from news_analyst.models import NewsItem
from news_analyst.utils import extract_keywords, normalize_text

RISK_KEYWORDS = {
    "crisis",
    "conflicto",
    "alerta",
    "emergencia",
    "inflacion",
    "tension",
    "ciberseguridad",
}
OPPORTUNITY_KEYWORDS = {"inversion", "crecimiento", "acuerdo", "innovacion", "avance"}


@dataclass
class SegmentAnalysis:
    segment_key: str
    segment_display_name: str
    executive_summary: str
    deep_analysis: str
    trends: List[str]
    risks: List[str]
    opportunities: List[str]
    implications: List[str]
    items: List[NewsItem]


def analyze_segment(segment_key: str, segment_display_name: str, items: List[NewsItem]) -> SegmentAnalysis:
    if not items:
        return SegmentAnalysis(
            segment_key=segment_key,
            segment_display_name=segment_display_name,
            executive_summary="No se identificaron noticias relevantes en el periodo analizado.",
            deep_analysis="La ausencia de noticias destacadas sugiere estabilidad temporal o baja cobertura.",
            trends=[],
            risks=[],
            opportunities=[],
            implications=["Monitorear nuevamente en el siguiente periodo."],
            items=[],
        )

    titles = [item.title for item in items]
    keywords = extract_keywords(titles, limit=6)
    joined_text = " ".join(normalize_text(title) for title in titles)

    risks = [
        f"Riesgo potencial asociado a '{keyword}'." for keyword in keywords if keyword in RISK_KEYWORDS
    ]
    opportunities = [
        f"Oportunidad emergente relacionada con '{keyword}'." for keyword in keywords
        if keyword in OPPORTUNITY_KEYWORDS
    ]
    if not risks and any(word in joined_text for word in RISK_KEYWORDS):
        risks.append("Indicadores de riesgo moderado en el segmento.")
    if not opportunities and any(word in joined_text for word in OPPORTUNITY_KEYWORDS):
        opportunities.append("Se observan señales de oportunidad o crecimiento.")

    executive_summary = (
        f"Se analizaron {len(items)} noticias. Los temas dominantes incluyen: "
        f"{', '.join(keywords) if keywords else 'eventos diversos'}."
    )
    deep_analysis = (
        "El segmento muestra variaciones en cobertura y relevancia. "
        "Se recomienda seguimiento cercano de actores y factores clave."
    )
    implications = [
        "Implicaciones potenciales para actores públicos y privados.",
        "Revisar impactos en decisiones estratégicas a corto plazo.",
    ]

    return SegmentAnalysis(
        segment_key=segment_key,
        segment_display_name=segment_display_name,
        executive_summary=executive_summary,
        deep_analysis=deep_analysis,
        trends=keywords,
        risks=risks,
        opportunities=opportunities,
        implications=implications,
        items=items,
    )
