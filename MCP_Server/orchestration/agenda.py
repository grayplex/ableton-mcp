"""Production agenda catalog: genre-specific ordered phase lists.

AGENDA_CATALOG maps genre_id -> list of phase definition dicts.
get_agenda(genre, brief) returns a ProductionAgenda TypedDict.
"""

import copy
import json
import logging
import re

from MCP_Server.genres.catalog import get_blueprint, resolve_alias
from MCP_Server.orchestration.schema import ProductionAgenda, ProductionPhase

logger = logging.getLogger("AbletonMCPServer")

# ---------------------------------------------------------------------------
# Estimated steps per phase type (D-04 from CONTEXT.md)
# ---------------------------------------------------------------------------

_ESTIMATED_STEPS = {
    "setup": 8,
    "drums": 12,
    "bass": 8,
    "harmony": 10,
    "melody": 8,
    "sound_design": 10,
    "arrangement": 6,
    "mix": 8,
    "master": 3,
}

# ---------------------------------------------------------------------------
# Phase goal strings per phase type
# ---------------------------------------------------------------------------

_PHASE_GOALS = {
    "setup": "Tempo, key, scale, tracks",
    "drums": "Kick, snare, hi-hats",
    "bass": "Bass line and groove",
    "harmony": "Chords and pads",
    "melody": "Lead melody",
    "sound_design": "Timbres and effects",
    "arrangement": "Drops, builds, transitions",
    "mix": "EQ, compression, levels",
    "master": "Master bus polish",
}

# ---------------------------------------------------------------------------
# Phase names per type (can be genre-flavored via overrides)
# ---------------------------------------------------------------------------

_PHASE_NAMES = {
    "setup": "Setup",
    "drums": "Drums",
    "bass": "Bass",
    "harmony": "Harmony",
    "melody": "Melody",
    "sound_design": "Sound Design",
    "arrangement": "Arrangement",
    "mix": "Mix",
    "master": "Master",
}

# ---------------------------------------------------------------------------
# Ambient-specific phase name overrides
# ---------------------------------------------------------------------------

_AMBIENT_NAME_OVERRIDES = {
    "harmony": "Pads",
    "sound_design": "Textures",
}

# ---------------------------------------------------------------------------
# True musical dependency map (PARA-01)
# Maps phase_type -> list of phase_types that must be complete before this one.
# These are filtered at get_agenda() time to only include types present in the
# genre's agenda, so genres that lack certain phases are handled automatically.
# ---------------------------------------------------------------------------

_PHASE_DEPS = {
    "setup":        [],                                                    # root — no prerequisites
    "drums":        ["setup"],                                             # only needs tempo/key from setup
    "bass":         ["setup"],                                             # only needs tempo/key from setup
    "harmony":      ["setup"],                                             # only needs key/scale from setup
    "melody":       ["setup"],                                             # only needs key/scale from setup
    "sound_design": ["setup"],                                             # timbre work, no content dependency
    "arrangement":  ["drums", "bass", "harmony", "melody", "sound_design"],  # needs all content phases
    "mix":          ["arrangement"],                                       # needs arrangement done
    "master":       ["mix"],                                               # needs mix done
}

# ---------------------------------------------------------------------------
# Role filter sets per phase type (D-05 from CONTEXT.md)
# ---------------------------------------------------------------------------

_DRUM_ROLES = {"kick", "snare", "hi-hats", "clap", "percussion", "808_bass", "rim", "cymbal"}
_BASS_ROLES = {"bass", "808_bass", "sub"}
_HARMONY_ROLES = {"pad", "chord", "stab", "strings", "piano", "keys", "guitar", "organ", "vinyl_noise"}
_MELODY_ROLES = {"lead", "melody", "vocal", "vocal_chop", "flute", "bell", "arp"}

def _filter_roles(all_roles: list, phase_type: str) -> list:
    """Return genre roles relevant to this phase type.

    Utility phases (setup, arrangement, mix, master) return an empty list
    to keep the serialized agenda under the token budget for all genres.
    Role lists are capped to limit JSON size; the parallelizable field and
    extended arrangement depends_on list consume additional budget.
    """
    if phase_type == "drums":
        filtered = [r for r in all_roles if r in _DRUM_ROLES]
        return filtered[:3]
    elif phase_type == "bass":
        return [r for r in all_roles if r in _BASS_ROLES][:2]
    elif phase_type == "harmony":
        return [r for r in all_roles if r in _HARMONY_ROLES][:3]
    elif phase_type == "melody":
        return [r for r in all_roles if r in _MELODY_ROLES][:2]
    elif phase_type in ("setup", "arrangement", "mix", "master"):
        return []
    else:  # sound_design — everything not already in drums/bass/harmony/melody
        already_typed = _DRUM_ROLES | _BASS_ROLES | _HARMONY_ROLES | _MELODY_ROLES
        return [r for r in all_roles if r not in already_typed][:2]


# ---------------------------------------------------------------------------
# AGENDA_CATALOG — 12 genre phase orderings
# Maps genre_id -> list of phase_type strings in execution order
# ---------------------------------------------------------------------------

AGENDA_CATALOG = {
    "house":        ["setup", "drums", "bass", "harmony", "melody", "arrangement", "sound_design", "mix", "master"],
    "techno":       ["setup", "drums", "bass", "sound_design", "arrangement", "mix", "master"],
    "ambient":      ["setup", "harmony", "sound_design", "arrangement", "mix", "master"],
    "hip_hop_trap": ["setup", "drums", "bass", "harmony", "melody", "arrangement", "mix", "master"],
    "drum_and_bass": ["setup", "drums", "bass", "melody", "arrangement", "sound_design", "mix", "master"],
    "dubstep":      ["setup", "drums", "bass", "sound_design", "melody", "arrangement", "mix", "master"],
    "trance":       ["setup", "drums", "bass", "harmony", "melody", "sound_design", "arrangement", "mix", "master"],
    "synthwave":    ["setup", "drums", "bass", "harmony", "melody", "sound_design", "arrangement", "mix", "master"],
    "future_bass":  ["setup", "drums", "harmony", "bass", "melody", "sound_design", "arrangement", "mix", "master"],
    "lo_fi":        ["setup", "drums", "bass", "harmony", "melody", "arrangement", "mix", "master"],
    "neo_soul_rnb": ["setup", "harmony", "bass", "drums", "melody", "arrangement", "sound_design", "mix", "master"],
    "disco_funk":   ["setup", "drums", "bass", "harmony", "melody", "arrangement", "mix", "master"],
}


def _build_phase(phase_type: str, all_roles: list, depends_on: list,
                 name_overrides: dict = None, parallelizable: bool = False) -> ProductionPhase:
    """Build a ProductionPhase dict for the given phase_type."""
    name = (name_overrides or {}).get(phase_type, _PHASE_NAMES[phase_type])
    return ProductionPhase(
        name=name,
        phase_id=phase_type,
        phase_type=phase_type,
        goal=_PHASE_GOALS[phase_type],
        roles=_filter_roles(all_roles, phase_type),
        estimated_steps=_ESTIMATED_STEPS[phase_type],
        depends_on=depends_on,
        parallelizable=parallelizable,
    )


def get_agenda(genre: str, brief: dict = None) -> dict:
    """Return a ProductionAgenda for the given genre.

    Args:
        genre: Genre id or alias.
        brief: Optional ProductionBrief dict. If brief["primary_genre"] is set,
               it overrides the genre arg. If brief["energy_level"] >= 7, drums
               phase is moved to position 1 (after setup).

    Returns:
        ProductionAgenda dict or {"error": "..."} on unknown genre.
    """
    # Resolve genre from brief.primary_genre first, then genre arg
    effective_genre = genre
    energy_level = 0
    if brief:
        if isinstance(brief, str):
            try:
                brief = json.loads(brief)
            except (json.JSONDecodeError, TypeError):
                brief = {}
        pg = brief.get("primary_genre")
        if pg:
            effective_genre = pg
        energy_level = brief.get("energy_level", 0) or 0

    # Normalize alias
    resolved = resolve_alias(effective_genre)
    if resolved is None:
        return {"error": f"Unknown genre '{effective_genre}'. Use list_genre_blueprints() to see available genres."}
    genre_id = resolved["genre_id"]

    if genre_id not in AGENDA_CATALOG:
        return {"error": f"No agenda defined for genre '{genre_id}'."}

    # Get blueprint for roles
    blueprint = get_blueprint(genre_id)
    all_roles = blueprint.get("instrumentation", {}).get("roles", []) if blueprint else []

    # Genre-specific name overrides
    name_overrides = _AMBIENT_NAME_OVERRIDES if genre_id == "ambient" else {}

    # Build phases with dependency chain
    phase_types = AGENDA_CATALOG[genre_id]

    # High-energy brief: ensure drums is phase index 1 (after setup)
    if energy_level >= 7 and "drums" in phase_types:
        drums_idx = phase_types.index("drums")
        if drums_idx > 1:
            phase_types = list(phase_types)
            phase_types.pop(drums_idx)
            phase_types.insert(1, "drums")

    phases = []
    phase_types_set = set(phase_types)
    for phase_type in phase_types:
        raw_deps = _PHASE_DEPS.get(phase_type, [])
        depends_on = [d for d in raw_deps if d in phase_types_set]
        parallelizable = depends_on == ["setup"]
        phase = _build_phase(phase_type, all_roles, depends_on, name_overrides, parallelizable)
        phases.append(phase)

    total_steps = sum(p["estimated_steps"] for p in phases)

    return ProductionAgenda(
        genre=genre_id,
        phases=phases,
        total_estimated_steps=total_steps,
    )


# ---------------------------------------------------------------------------
# refine_agenda — modify an existing ProductionAgenda with a natural-language
# instruction, without regenerating from scratch.
# ---------------------------------------------------------------------------

# Known phase types, used for matching skip/add instructions.
_ALL_PHASE_TYPES = list(_ESTIMATED_STEPS.keys())

# Alias map for instruction words -> canonical phase_type
_PHASE_TYPE_ALIASES = {
    "mastering": "master",
    "mixing": "mix",
    "drumming": "drums",
}

# Pattern: "skip|remove|no <phase_type or alias>"
_ALL_PHASE_WORDS = list(_ALL_PHASE_TYPES) + list(_PHASE_TYPE_ALIASES.keys())
_SKIP_PATTERN = re.compile(
    r"\b(?:skip|remove|no)\s+(" + "|".join(_ALL_PHASE_WORDS) + r")\b"
)

# Pattern: "add (a )?(second|another) <phase_type>" or "duplicate <phase_type>"
_ADD_PATTERN = re.compile(
    r"\b(?:add\s+(?:a\s+)?(?:second|another)\s+(" + "|".join(_ALL_PHASE_WORDS) + r")"
    r"|duplicate\s+(" + "|".join(_ALL_PHASE_WORDS) + r"))\b"
)


def refine_agenda(agenda: dict, instruction: str) -> dict:
    """Modify an existing ProductionAgenda with a natural-language instruction.

    Supported instructions (case-insensitive):
      - "skip <phase_type>" / "remove <phase_type>" / "no <phase_type>":
        Removes all phases with the given phase_type.
      - "add a second <phase_type>" / "add another <phase_type>" /
        "duplicate <phase_type>":
        Appends a copy of the first matching phase as "<phase_type>_2",
        inserted immediately after the original in the phases list.

    Unrecognised instructions return the original agenda unchanged (no mutation).
    total_estimated_steps is always recomputed after any modification.

    Returns:
        A new ProductionAgenda dict (never mutates the input).
    """
    norm = instruction.lower().strip()

    # --- skip / remove / no <phase_type> ---
    skip_match = _SKIP_PATTERN.search(norm)
    if skip_match:
        target = _PHASE_TYPE_ALIASES.get(skip_match.group(1), skip_match.group(1))
        new_phases = [p for p in agenda["phases"] if p["phase_type"] != target]
        new_steps = sum(p["estimated_steps"] for p in new_phases)
        return dict(agenda, phases=new_phases, total_estimated_steps=new_steps)

    # --- add a second / duplicate <phase_type> ---
    add_match = _ADD_PATTERN.search(norm)
    if add_match:
        raw_target = add_match.group(1) or add_match.group(2)
        target = _PHASE_TYPE_ALIASES.get(raw_target, raw_target)
        # Find the source phase
        source_idx = next(
            (i for i, p in enumerate(agenda["phases"]) if p["phase_type"] == target),
            None,
        )
        if source_idx is not None:
            new_phases = list(agenda["phases"])
            new_phase = copy.deepcopy(new_phases[source_idx])
            new_phase["phase_id"] = f"{target}_2"
            new_phase["depends_on"] = [new_phases[source_idx]["phase_id"]]
            new_phases.insert(source_idx + 1, new_phase)
            new_steps = sum(p["estimated_steps"] for p in new_phases)
            return dict(agenda, phases=new_phases, total_estimated_steps=new_steps)

    # Unrecognised instruction — return unchanged
    return agenda
