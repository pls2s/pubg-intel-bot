from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher


def normalize_text(value: str) -> str:
    """Normalize user input for English and Thai keyword matching."""

    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w\u0E00-\u0E7F]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def similarity(query: str, candidate: str) -> float:
    query_norm = normalize_text(query)
    candidate_norm = normalize_text(candidate)
    if not query_norm or not candidate_norm:
        return 0.0

    if candidate_norm in query_norm:
        return 1.0
    if query_norm in candidate_norm:
        return 0.92

    query_tokens = set(query_norm.split())
    candidate_tokens = set(candidate_norm.split())
    if query_tokens and candidate_tokens:
        overlap = len(query_tokens & candidate_tokens) / len(candidate_tokens)
    else:
        overlap = 0.0

    fuzzy = SequenceMatcher(None, query_norm, candidate_norm).ratio()
    return max(fuzzy, overlap)


def command_args(text: str | None) -> str:
    if not text:
        return ""
    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""
