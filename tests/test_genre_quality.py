"""Centralized quality gate: token budget and theory-name cross-validation for all genres."""

import json

import pytest
import tiktoken

from MCP_Server.genres import get_blueprint, list_genres
from MCP_Server.theory.chords import _QUALITY_MAP
from MCP_Server.theory.scales import SCALE_CATALOG


def _all_blueprints():
    """Yield (label, blueprint) for every genre and subgenre."""
    for genre_info in list_genres():
        genre_id = genre_info["id"]
        bp = get_blueprint(genre_id)
        yield (genre_id, bp)
        for sub_id in genre_info.get("subgenres", []):
            sub_bp = get_blueprint(genre_id, sub_id)
            if sub_bp is not None:
                yield (f"{genre_id}/{sub_id}", sub_bp)


# ---------------------------------------------------------------------------
# QUAL-01: Token budget validation
# ---------------------------------------------------------------------------


class TestTokenBudget:
    """Verify every genre blueprint stays within the token budget."""

    _MAX_TOKENS_OVERRIDE: dict = {
        # "genre_id": max_tokens  -- add only if genre genuinely needs >1200
    }
    DEFAULT_MIN_TOKENS = 400
    DEFAULT_MAX_TOKENS = 1200

    def test_all_genres_within_token_budget(self):
        enc = tiktoken.get_encoding("cl100k_base")
        failures = []
        for genre_info in list_genres():
            genre_id = genre_info["id"]
            bp = get_blueprint(genre_id)
            token_count = len(enc.encode(json.dumps(bp)))
            max_tokens = self._MAX_TOKENS_OVERRIDE.get(genre_id, self.DEFAULT_MAX_TOKENS)
            if not (self.DEFAULT_MIN_TOKENS <= token_count <= max_tokens):
                failures.append(f"{genre_id}: {token_count} tokens")
        assert not failures, (
            f"Genres outside token budget ({self.DEFAULT_MIN_TOKENS}-{self.DEFAULT_MAX_TOKENS}):\n"
            + "\n".join(failures)
        )

    def test_genre_count(self):
        assert len(list_genres()) == 12


# ---------------------------------------------------------------------------
# QUAL-02: Theory name cross-validation
# ---------------------------------------------------------------------------


class TestTheoryNameCrossValidation:
    """Verify all chord_types and scale names reference valid theory engine entries."""

    def test_all_chord_types_valid(self):
        failures = []
        for label, bp in _all_blueprints():
            harmony = bp.get("harmony")
            if harmony is None:
                continue
            for ct in harmony.get("chord_types", []):
                if ct not in _QUALITY_MAP:
                    failures.append((label, ct))
        assert not failures, (
            "Invalid chord types found:\n"
            + "\n".join(f"  {label}: {ct}" for label, ct in failures)
        )

    def test_all_scale_names_valid(self):
        failures = []
        for label, bp in _all_blueprints():
            harmony = bp.get("harmony")
            if harmony is None:
                continue
            for s in harmony.get("scales", []):
                if s not in SCALE_CATALOG:
                    failures.append((label, s))
        assert not failures, (
            "Invalid scale names found:\n"
            + "\n".join(f"  {label}: {s}" for label, s in failures)
        )

    def test_all_genres_have_harmony(self):
        missing = []
        for genre_info in list_genres():
            genre_id = genre_info["id"]
            bp = get_blueprint(genre_id)
            harmony = bp.get("harmony")
            if harmony is None:
                missing.append(f"{genre_id}: missing harmony section")
                continue
            for key in ("scales", "chord_types", "common_progressions"):
                if key not in harmony:
                    missing.append(f"{genre_id}: missing harmony.{key}")
        assert not missing, "Harmony issues:\n" + "\n".join(missing)


# ---------------------------------------------------------------------------
# QUAL-03: Structural coverage
# ---------------------------------------------------------------------------


class TestQualityCoverage:
    """Structural coverage: schema validation, tool output format, section filtering."""

    def test_schema_validation_exists(self):
        from MCP_Server.genres.schema import validate_blueprint  # noqa: F401

    def test_tool_output_format(self):
        genres = list_genres()
        for g in genres:
            assert "id" in g, f"Missing 'id' key in genre entry"
            assert "name" in g, f"Missing 'name' key in genre entry"
            assert "bpm_range" in g, f"Missing 'bpm_range' key in genre entry"
            assert "subgenres" in g, f"Missing 'subgenres' key in genre entry"

    def test_section_filtering(self):
        bp = get_blueprint("house")
        assert bp is not None
        for dim in (
            "instrumentation",
            "harmony",
            "rhythm",
            "arrangement",
            "mixing",
            "production_tips",
        ):
            assert dim in bp, f"Missing dimension: {dim}"
