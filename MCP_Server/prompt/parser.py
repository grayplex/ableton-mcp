"""Prompt parser: tokenize and classify a free-text music prompt into a SignalSet.

Algorithm:
1. Normalize input: lowercase, replace hyphens/underscores/punctuation with spaces.
2. Build word list. Try longest alias matches first (greedy left-to-right scan).
3. For each unmatched word, try single-token lookup in each map by priority:
   genre → instrument → effect → mood → tempo → structural.
4. Unrecognized tokens (len > 2) → raw_descriptors.
5. Compute confidence from signal richness.

No derivation happens here — only signal classification.
"""

import re
from typing import Optional

from MCP_Server.prompt.lexicon import (
    EFFECT_MAP,
    GENRE_MAP,
    GROOVE_HINTS,
    INSTRUMENT_MAP,
    MOOD_MAP,
    STRUCTURAL_HINTS,
    TEMPO_MAP,
)
# Expose for use in deriver (checks structural_hints list for groove override keys)
__all__ = ["classify_prompt"]
from MCP_Server.prompt.schema import SignalSet

# ---------------------------------------------------------------------------
# Build sorted multi-word alias list for greedy longest-match scanning.
# Each entry: (word_list, signal_type, value)
# Sorted by word count descending so longest phrases match first.
# ---------------------------------------------------------------------------

_MULTI_WORD_LOOKUPS: list[tuple[list[str], str, object]] = []


def _build_multi_word_table() -> None:
    """Populate _MULTI_WORD_LOOKUPS from all lexicon maps."""
    entries = []

    for alias, genre_id in GENRE_MAP.items():
        words = alias.split("_")
        if len(words) >= 2:
            entries.append((words, "genre", genre_id))

    for alias, val in INSTRUMENT_MAP.items():
        words = alias.split("_")
        if len(words) >= 2:
            entries.append((words, "instrument", val))

    for alias, val in EFFECT_MAP.items():
        words = alias.split("_")
        if len(words) >= 2:
            entries.append((words, "effect", val))

    for alias, val in MOOD_MAP.items():
        words = alias.split("_")
        if len(words) >= 2:
            entries.append((words, "mood", val))

    # GROOVE_HINTS multi-word phrases (e.g. "four_on_the_floor" → "four on the floor")
    for alias in GROOVE_HINTS:
        words = alias.split("_")
        if len(words) >= 2:
            entries.append((words, "structural", alias))

    # Sort by word count descending for longest-match-first
    entries.sort(key=lambda e: -len(e[0]))
    _MULTI_WORD_LOOKUPS.extend(entries)


_build_multi_word_table()


# ---------------------------------------------------------------------------
# Stop words to skip (very short, semantically empty in music context)
# ---------------------------------------------------------------------------

_STOP_WORDS = {"a", "an", "the", "in", "on", "of", "for", "with", "or", "to", "at",
               "is", "it", "its", "be", "by"}
# "and" intentionally excluded from stop words — needed for "drum and bass" phrase matching


def _normalize_prompt(text: str) -> list[str]:
    """Normalize text to a list of lowercase word tokens.

    Replaces hyphens, underscores, slashes, and extra whitespace with spaces.
    Strips punctuation from word boundaries.
    Stop words are preserved in the token stream for multi-word phrase matching
    (e.g. "drum and bass") but are not reported as raw_descriptors.
    """
    # Replace separators (except hyphens — handled below) with spaces
    normalized = re.sub(r"[-_/+]", " ", text.lower())
    # Strip leading/trailing punctuation from each token
    tokens = [re.sub(r"^[^\w]+|[^\w]+$", "", t) for t in normalized.split()]
    # Remove empty tokens only — stop words stay for phrase matching
    return [t for t in tokens if t]


def _compute_confidence(
    genre_signals: list,
    mood_signals: list,
    instrument_signals: list,
    effect_signals: list,
) -> float:
    """Compute parse confidence based on signal richness.

    Base confidence from genre detection; additional signals add small bonuses.
    Returns 0.0 when no meaningful signals were found.
    """
    if not genre_signals and not mood_signals and not instrument_signals and not effect_signals:
        return 0.0

    score = 0.0
    if genre_signals:
        score += 0.70
    if mood_signals:
        score += 0.10
    if instrument_signals:
        score += 0.07
    if effect_signals:
        score += 0.05
    # Low-confidence case: only mood/instrument without genre
    if not genre_signals:
        score = min(score, 0.45)

    return round(min(score, 0.95), 2)


def classify_prompt(text: str) -> SignalSet:
    """Classify a free-text music prompt into a SignalSet.

    Extracts genre, mood, instrument, effect, tempo, and structural signals
    using greedy longest-match tokenization against the signal lexicon.
    Unrecognized tokens (length > 2) are passed through as raw_descriptors.

    Returns an empty SignalSet with confidence=0.0 for empty input.
    """
    if not text or not text.strip():
        return SignalSet(
            genre_signals=[],
            mood_signals=[],
            instrument_signals=[],
            effect_signals=[],
            tempo_signals=[],
            structural_hints=[],
            raw_descriptors=[],
            confidence=0.0,
        )

    words = _normalize_prompt(text)
    if not words:
        return SignalSet(
            genre_signals=[],
            mood_signals=[],
            instrument_signals=[],
            effect_signals=[],
            tempo_signals=[],
            structural_hints=[],
            raw_descriptors=[],
            confidence=0.0,
        )

    genre_signals: list = []
    mood_signals: list = []
    instrument_signals: list = []
    effect_signals: list = []
    tempo_signals: list = []
    structural_hints: list = []
    raw_descriptors: list = []

    consumed: set[int] = set()
    n = len(words)

    # --- Pass 1: greedy multi-word matching (longest phrase first) ---
    for phrase_words, sig_type, value in _MULTI_WORD_LOOKUPS:
        phrase_len = len(phrase_words)
        for start in range(n - phrase_len + 1):
            # Skip if any position already consumed
            if any(start + j in consumed for j in range(phrase_len)):
                continue
            if words[start:start + phrase_len] == phrase_words:
                _record_signal(
                    sig_type, value,
                    genre_signals, mood_signals, instrument_signals,
                    effect_signals, structural_hints,
                )
                for j in range(phrase_len):
                    consumed.add(start + j)
                break  # move to next phrase pattern

    # --- Pass 2: single-token matching for unconsumed words ---
    for i, word in enumerate(words):
        if i in consumed:
            continue

        matched = _try_single_token(
            word,
            genre_signals, mood_signals, instrument_signals,
            effect_signals, tempo_signals, structural_hints,
        )
        if matched:
            consumed.add(i)
        elif word not in _STOP_WORDS and len(word) > 2:
            raw_descriptors.append(word)

    confidence = _compute_confidence(
        genre_signals, mood_signals, instrument_signals, effect_signals
    )

    return SignalSet(
        genre_signals=genre_signals,
        mood_signals=mood_signals,
        instrument_signals=instrument_signals,
        effect_signals=effect_signals,
        tempo_signals=tempo_signals,
        structural_hints=structural_hints,
        raw_descriptors=raw_descriptors,
        confidence=confidence,
    )


def _record_signal(
    sig_type: str,
    value: object,
    genre_signals: list,
    mood_signals: list,
    instrument_signals: list,
    effect_signals: list,
    structural_hints: list,
) -> None:
    """Append a matched signal to the appropriate list (deduplicating genres)."""
    if sig_type == "genre":
        if value not in genre_signals:
            genre_signals.append(value)
    elif sig_type == "instrument":
        instrument_signals.append(dict(value))
    elif sig_type == "effect":
        if value not in effect_signals:
            effect_signals.append(value)
    elif sig_type == "mood":
        mood_signals.append(dict(value))
    elif sig_type == "structural":
        if value not in structural_hints:
            structural_hints.append(value)


def _try_single_token(
    word: str,
    genre_signals: list,
    mood_signals: list,
    instrument_signals: list,
    effect_signals: list,
    tempo_signals: list,
    structural_hints: list,
) -> bool:
    """Try to classify a single word token. Returns True if matched."""
    # Priority: genre > instrument > effect > mood > tempo > structural

    if word in GENRE_MAP:
        genre_id = GENRE_MAP[word]
        if genre_id not in genre_signals:
            genre_signals.append(genre_id)
        return True

    if word in INSTRUMENT_MAP:
        instrument_signals.append(dict(INSTRUMENT_MAP[word]))
        return True

    if word in EFFECT_MAP:
        effect = EFFECT_MAP[word]
        if effect not in effect_signals:
            effect_signals.append(effect)
        return True

    if word in MOOD_MAP:
        mood_signals.append({**MOOD_MAP[word], "term": word})
        return True

    if word in TEMPO_MAP:
        tempo_signals.append({"term": word, "bpm_modifier": TEMPO_MAP[word]})
        return True

    if word in STRUCTURAL_HINTS or word in GROOVE_HINTS:
        if word not in structural_hints:
            structural_hints.append(word)
        return True

    return False
