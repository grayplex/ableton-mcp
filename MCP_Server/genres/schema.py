"""Genre blueprint schema: TypedDict definitions and import-time validation.

Defines the data contract that all genre blueprint files must conform to.
The catalog (plan 02) calls validate_blueprint() during auto-discovery to
ensure every registered genre matches GenreBlueprint's shape.

Per D-06: TypedDict for schema definition.
Per D-07: validate_blueprint() checks required keys and types at import time.
Per D-08: Caller catches ValueError per genre (fail per-genre, not per-server).
Per D-09: All dimensions use structured data with typed fields, no prose.
"""

from typing import List, TypedDict


# ---------------------------------------------------------------------------
# Section TypedDicts — one per blueprint dimension
# ---------------------------------------------------------------------------

class InstrumentationSection(TypedDict):
    """Instrument roles for the genre (generic names, not device-specific per D-11)."""
    roles: List[str]  # e.g., ["kick", "bass", "pad", "lead", "hi-hats"]


class HarmonySection(TypedDict):
    """Harmonic conventions — scales, chord types, and progressions (per D-10)."""
    scales: List[str]           # Scale names matching SCALE_CATALOG keys
    chord_types: List[str]      # Chord quality names matching _QUALITY_MAP keys
    common_progressions: List[List[str]]  # Roman numeral sequences


class RhythmSection(TypedDict):
    """Rhythmic conventions — tempo, time signature, swing, patterns."""
    time_signature: str         # e.g., "4/4"
    bpm_range: List[int]        # [min, max]
    swing: str                  # e.g., "none", "light", "heavy"
    note_values: List[str]      # e.g., ["1/4", "1/8", "1/16"]
    drum_pattern: str           # Brief description, e.g., "four-on-the-floor kick"


class _ArrangementEntryRequired(TypedDict):
    """Required fields for arrangement entries."""
    name: str   # Section name, e.g., "intro"
    bars: int   # Number of bars


class ArrangementEntry(_ArrangementEntryRequired, total=False):
    """A single section in an arrangement (per D-12).

    Required: name, bars
    Optional: energy, roles, transition_in (added in v1.3 Phase 25)
    """
    energy: int          # 1-10 energy level for this section
    roles: List[str]     # Active instrument roles in this section
    transition_in: str   # How to transition into this section


class ArrangementSection(TypedDict):
    """Arrangement structure — ordered sections with bar counts (per D-12)."""
    sections: List[ArrangementEntry]


class MixingSection(TypedDict):
    """Mixing conventions — frequency, stereo, effects, compression."""
    frequency_focus: str        # e.g., "low-end emphasis with sub-bass"
    stereo_field: str           # e.g., "wide pads, mono bass"
    common_effects: List[str]   # e.g., ["sidechain compression", "reverb"]
    compression_style: str      # e.g., "heavy sidechain on bass/pads"


class ProductionTipsSection(TypedDict):
    """Genre-specific production advice."""
    techniques: List[str]       # Production techniques
    pitfalls: List[str]         # Common mistakes to avoid


# ---------------------------------------------------------------------------
# Top-level blueprint TypedDict
# ---------------------------------------------------------------------------

class GenreBlueprint(TypedDict):
    """Complete genre blueprint — the data contract for all genre files."""
    name: str                               # Display name, e.g., "House"
    id: str                                 # Canonical identifier, e.g., "house"
    bpm_range: List[int]                    # [min, max]
    aliases: List[str]                      # Alternative names for alias resolution
    instrumentation: InstrumentationSection
    harmony: HarmonySection
    rhythm: RhythmSection
    arrangement: ArrangementSection
    mixing: MixingSection
    production_tips: ProductionTipsSection


# ---------------------------------------------------------------------------
# Required keys for each section (used by validate_blueprint)
# ---------------------------------------------------------------------------

_REQUIRED_TOP_LEVEL = [
    "name", "id", "bpm_range", "aliases",
    "instrumentation", "harmony", "rhythm",
    "arrangement", "mixing", "production_tips",
]

_SECTION_SPEC = {
    "instrumentation": {
        "required": {"roles": (list, True)},  # (type, must_be_nonempty)
    },
    "harmony": {
        "required": {
            "scales": (list, True),
            "chord_types": (list, True),
            "common_progressions": (list, True),
        },
    },
    "rhythm": {
        "required": {
            "time_signature": (str, False),
            "bpm_range": (list, False),
            "swing": (str, False),
            "note_values": (list, True),
            "drum_pattern": (str, False),
        },
    },
    "arrangement": {
        "required": {"sections": (list, True)},
    },
    "mixing": {
        "required": {
            "frequency_focus": (str, False),
            "stereo_field": (str, False),
            "common_effects": (list, True),
            "compression_style": (str, False),
        },
    },
    "production_tips": {
        "required": {
            "techniques": (list, True),
            "pitfalls": (list, True),
        },
    },
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_blueprint(data: dict) -> None:
    """Validate a genre blueprint dict against the required schema.

    Raises ValueError if data is malformed. Returns None on success.
    Per D-07: checks required keys and types at import time.
    Per D-08: caller (catalog) catches ValueError per genre.
    """
    # Must be a dict
    if not isinstance(data, dict):
        raise ValueError("Blueprint must be a dict")

    # Check required top-level keys
    for key in _REQUIRED_TOP_LEVEL:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    # Top-level type checks
    if not isinstance(data["name"], str):
        raise ValueError("'name' must be a string")
    if not isinstance(data["id"], str):
        raise ValueError("'id' must be a string")
    if not isinstance(data["aliases"], list):
        raise ValueError("'aliases' must be a list")

    # bpm_range: list of exactly 2 ints
    _check_bpm_range(data["bpm_range"], "bpm_range")

    # Validate each section
    for section_name, spec in _SECTION_SPEC.items():
        section_data = data[section_name]
        if not isinstance(section_data, dict):
            raise ValueError(f"'{section_name}' must be a dict")

        for field, (expected_type, must_be_nonempty) in spec["required"].items():
            if field not in section_data:
                raise ValueError(
                    f"Missing required key '{field}' in '{section_name}'"
                )
            value = section_data[field]
            if not isinstance(value, expected_type):
                raise ValueError(
                    f"'{field}' in '{section_name}' must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )
            if must_be_nonempty and isinstance(value, list) and len(value) == 0:
                raise ValueError(
                    f"'{field}' in '{section_name}' must not be empty"
                )

    # rhythm.bpm_range: list of exactly 2 ints
    _check_bpm_range(data["rhythm"]["bpm_range"], "rhythm.bpm_range")

    # arrangement.sections entries: each must have 'name' (str) and 'bars' (int)
    for i, entry in enumerate(data["arrangement"]["sections"]):
        if not isinstance(entry, dict):
            raise ValueError(f"arrangement.sections[{i}] must be a dict")
        if "name" not in entry or not isinstance(entry["name"], str):
            raise ValueError(f"arrangement.sections[{i}] must have 'name' (str)")
        if "bars" not in entry or not isinstance(entry["bars"], int):
            raise ValueError(f"arrangement.sections[{i}] must have 'bars' (int)")
        # Optional v1.3 fields: validate type/range if present
        if "energy" in entry:
            if not isinstance(entry["energy"], int) or not (1 <= entry["energy"] <= 10):
                raise ValueError(
                    f"arrangement.sections[{i}].energy must be int 1-10"
                )
        if "roles" in entry:
            if not isinstance(entry["roles"], list):
                raise ValueError(
                    f"arrangement.sections[{i}].roles must be a list"
                )
        if "transition_in" in entry:
            if not isinstance(entry["transition_in"], str):
                raise ValueError(
                    f"arrangement.sections[{i}].transition_in must be a string"
                )


def _check_bpm_range(value: object, label: str) -> None:
    """Validate that value is a list of exactly 2 ints."""
    if not isinstance(value, list):
        raise ValueError(f"'{label}' must be a list, got {type(value).__name__}")
    if len(value) != 2:
        raise ValueError(f"'{label}' must have exactly 2 elements (min, max)")
    if not all(isinstance(v, int) for v in value):
        raise ValueError(f"'{label}' elements must be integers")
