"""Data models for news_analyst."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    title: str
    source: str
    url: str
    published_at: Optional[datetime]
    author: Optional[str]
    summary: str
    content: str
    segment: str
    language: str
    consulted_at: datetime
    relevance_score: int
    relevance_reason: str
    source_type: str
    impact_level: str
    related_sources: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "author": self.author,
            "summary": self.summary,
            "content": self.content,
            "segment": self.segment,
            "language": self.language,
            "consulted_at": self.consulted_at.isoformat(),
            "relevance_score": self.relevance_score,
            "relevance_reason": self.relevance_reason,
            "source_type": self.source_type,
            "impact_level": self.impact_level,
            "related_sources": self.related_sources,
        }
