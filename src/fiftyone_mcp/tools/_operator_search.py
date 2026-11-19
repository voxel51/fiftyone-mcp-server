"""
Voxel51 operator search

Dependency-free field-weighted keyword scorer for narrowing
``list_operators``'s result by keyword instead of returning every
installed operator.

| Copyright 2017-2026, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

import re

MAX_RESULTS = 10
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_MAX_QUERY_CHARS = 256
_MAX_QUERY_TOKENS = 16
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "in",
        "on",
        "of",
        "to",
        "for",
        "and",
        "or",
        "is",
        "are",
        "was",
        "were",
        "be",
        "by",
        "with",
        "at",
        "from",
        "as",
        "it",
        "this",
        "that",
    }
)

_FIELD_WEIGHTS = (
    ("name", 3.0),
    ("label", 3.0),
    ("plugin_name", 1.5),
    ("description", 1.0),
)


def _tokenize(text) -> list[str]:
    return _TOKEN_RE.findall(str(text or "").lower())


def _query_tokens(query) -> list[str]:
    """Tokenizes a caller-supplied *query*, bounded (see
    ``_MAX_QUERY_*``) since this input is untrusted, unlike catalog
    operator text. Common English filler words (``_STOPWORDS``) are
    dropped since they appear in nearly every operator's description
    and would otherwise count as matches unrelated to the caller's
    actual intent."""
    truncated = str(query or "")[:_MAX_QUERY_CHARS]
    tokens = [
        token for token in _tokenize(truncated) if token not in _STOPWORDS
    ]
    return list(dict.fromkeys(tokens))[:_MAX_QUERY_TOKENS]


def has_terms(query) -> bool:
    """Whether *query* tokenizes to at least one search term.

    The single source of truth for "blank query" -- a caller-visible
    non-empty string (whitespace, punctuation-only, an emoji, a script
    ``_TOKEN_RE`` can't tokenize) can still carry zero terms, and
    callers must treat that the same as an empty query rather than
    passing it to :func:`search_operators`, which only ranks against
    real terms.
    """
    return bool(_query_tokens(query))


def _operator_fields(op) -> dict:
    return {
        "name": op.name,
        "label": op.config.label,
        "plugin_name": op.plugin_name,
        "description": op.config.description,
    }


def _score(query_tokens: list[str], op) -> float:
    fields = _operator_fields(op)
    result = 0.0
    for field, weight in _FIELD_WEIGHTS:
        text = fields.get(field) or ""
        text_tokens = set(_tokenize(text))
        text_lower = str(text).lower()
        for token in query_tokens:
            if token in text_tokens:
                result += weight
            elif token in text_lower:
                result += weight * 0.5
    return result


def search_operators(operators: list, query, limit: int = MAX_RESULTS) -> list:
    """Ranks *operators* (real operator objects, as returned by
    :func:`fiftyone.operators.registry.list_operators`) against *query*,
    capped at *limit*.

    Callers must check :func:`has_terms` themselves before calling this
    -- a *query* with no terms ranks against nothing and returns ``[]``,
    it is never treated as "browse the full list."
    """
    query_tokens = _query_tokens(query)
    if not query_tokens:
        return []
    scored = ((op, _score(query_tokens, op)) for op in operators)
    matches = sorted(
        (pair for pair in scored if pair[1] > 0),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return [op for op, _ in matches[:limit]]
