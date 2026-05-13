"""Utility helpers for news_analyst."""

from __future__ import annotations

import html
import re
import unicodedata
from collections import Counter
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable, Optional

STOPWORDS = {
    "de",
    "la",
    "el",
    "y",
    "a",
    "en",
    "del",
    "los",
    "las",
    "un",
    "una",
    "para",
    "por",
    "con",
    "sin",
    "sobre",
    "al",
    "se",
    "que",
    "su",
    "sus",
    "the",
    "and",
    "to",
    "of",
    "in",
    "on",
    "for",
    "at",
    "from",
    "by",
    "is",
    "are",
}


def strip_html(text: Optional[str]) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = html.unescape(clean)
    return re.sub(r"\s+", " ", clean).strip()


def normalize_text(text: str) -> str:
    text = strip_html(text).lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def extract_keywords(texts: Iterable[str], limit: int = 6) -> list[str]:
    counter: Counter[str] = Counter()
    for text in texts:
        for token in normalize_text(text).split():
            if len(token) < 4 or token in STOPWORDS:
                continue
            counter[token] += 1
    return [word for word, _ in counter.most_common(limit)]


def parse_datetime(value: object) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.utcfromtimestamp(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return parsedate_to_datetime(value)
        except (TypeError, ValueError):
            pass
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def ensure_parent_dir(path: str) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target
