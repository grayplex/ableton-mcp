"""Phase execution plan catalog: concrete ordered step lists per phase type and genre.

get_execution_plan(phase_name, genre, section_name, context) returns a PhaseChecklist
TypedDict with ExecutionStep entries — exact tool names and genre-appropriate suggested args.

Architecture (D-02):
1. _DEFAULT_STEPS[phase_type] — generic steps, built by factory functions
2. _DRUM_PATTERNS[genre_group] — MIDI note arrays per drum pattern group (D-04)
3. _GENRE_PARAMS[genre_id] — BPM midpoint, scale_name, instrument hints (D-05/D-08)
"""

import logging

from MCP_Server.genres.catalog import get_blueprint, resolve_alias
from MCP_Server.orchestration.schema import ExecutionStep, PhaseChecklist

logger = logging.getLogger("AbletonMCPServer")

# ---------------------------------------------------------------------------
# Drum pattern groups (D-04)
# ---------------------------------------------------------------------------

def _note(pitch, start_time, duration=0.25, velocity=100):
    return {"pitch": pitch, "start_time": start_time, "duration": duration, "velocity": velocity}


# Drum patterns — 1-bar seed patterns (extend with Ableton's loop/repeat).
# D-07 note budget: kick≤4, clap/snare≤2, hi-hat≤4 total per phase.
_DRUM_PATTERNS = {
    # House / Disco / Lo-fi — 4-on-floor (seed pattern; duplicate to fill bar)
    "house": {
        "kick_clap": [
            _note(36, 0.0, 0.25, 100), _note(36, 2.0, 0.25, 100),
            _note(39, 1.0, 0.1, 90),
        ],
        "hihat": [_note(42, 0.0, 0.25, 70), _note(42, 0.5, 0.25, 70)],
        "clap_pitch": 39,
    },
    # Techno / DnB — driving kick, no clap
    "techno": {
        "kick_clap": [
            _note(36, 0.0, 0.25, 110), _note(36, 1.0, 0.25, 110),
            _note(36, 2.0, 0.25, 110), _note(36, 3.0, 0.25, 110),
        ],
        "hihat": [_note(42, 0.0, 0.25, 75), _note(42, 0.5, 0.25, 75)],
        "clap_pitch": 38,
    },
    # Hip-hop / Trap — swing kick, hard snare, 16th hi-hats
    "hiphop": {
        "kick_clap": [
            _note(36, 0.0, 0.25, 110), _note(36, 2.5, 0.25, 110),
            _note(38, 1.0, 0.25, 100), _note(38, 3.0, 0.25, 100),
        ],
        "hihat": [
            _note(42, 0.0, 0.25, 65), _note(42, 0.25, 0.25, 65),
            _note(42, 0.5, 0.25, 65), _note(42, 0.75, 0.25, 65),
        ],
        "clap_pitch": 38,
    },
    # Dubstep — half-time feel
    "dubstep": {
        "kick_clap": [
            _note(36, 0.0, 0.25, 115), _note(36, 3.0, 0.25, 115),
            _note(38, 2.0, 0.25, 105),
        ],
        "hihat": [_note(42, 0.0, 0.25, 68), _note(42, 0.5, 0.25, 68)],
        "clap_pitch": 38,
    },
    # Trance / Synthwave / Future Bass
    "trance": {
        "kick_clap": [
            _note(36, 0.0, 0.25, 105), _note(36, 2.0, 0.25, 105),
            _note(39, 1.0, 0.1, 95),
        ],
        "hihat": [_note(42, 0.0, 0.25, 72), _note(42, 0.5, 0.25, 72)],
        "clap_pitch": 39,
    },
    # Neo-soul / R&B — swing feel, kick anticipation, snare on 2+4
    "neo_soul_rnb": {
        "kick_clap": [
            _note(36, 0.0, 0.25, 100),   # kick beat 1
            _note(36, 1.5, 0.25, 85),    # kick anticipation (and-of-2)
            _note(38, 1.0, 0.25, 100),   # snare beat 2
            _note(38, 3.0, 0.25, 100),   # snare beat 4
        ],
        "hihat": [
            _note(42, 0.0, 0.25, 65),    # hi-hat beat 1
            _note(42, 1.0, 0.25, 60),    # hi-hat beat 2
            _note(42, 2.0, 0.25, 65),    # hi-hat beat 3
            _note(42, 3.0, 0.25, 60),    # hi-hat beat 4
        ],
        "clap_pitch": 38,
    },
}

# ---------------------------------------------------------------------------
# Bass pattern groups (mirrors drum pattern architecture)
# ---------------------------------------------------------------------------

_BASS_PATTERNS = {
    # House / Disco / Lo-fi — Root-fifth pumping eighth-note pattern
    "house": [
        _note(36, 0.0, 0.5, 90), _note(36, 1.0, 0.25, 80),
        _note(36, 2.0, 0.5, 90), _note(41, 3.0, 0.5, 85),
    ],
    # Techno / DnB — Driving monotone root with short staccato hits
    "techno": [
        _note(36, 0.0, 0.25, 100), _note(36, 1.0, 0.25, 100),
        _note(36, 2.0, 0.25, 100), _note(36, 3.0, 0.25, 100),
    ],
    # Hip-hop / Trap — Syncopated 808 sub pattern, swing feel
    "hiphop": [
        _note(36, 0.0, 1.0, 100), _note(36, 1.5, 0.5, 85),
        _note(34, 2.5, 1.0, 95), _note(36, 3.5, 0.5, 80),
    ],
    # Dubstep — Half-time sub-bass with wide intervals for wobble feel
    "dubstep": [
        _note(36, 0.0, 1.5, 110), _note(29, 2.0, 1.0, 105),
        _note(36, 3.0, 0.5, 100), _note(31, 3.5, 0.5, 95),
    ],
    # Trance / Synthwave / Future Bass — Rolling arpeggiated bass
    "trance": [
        _note(36, 0.0, 0.5, 95), _note(48, 0.5, 0.5, 80),
        _note(43, 2.0, 0.5, 90), _note(36, 3.0, 1.0, 95),
    ],
    # Neo-soul / R&B — Smooth walking bass with chromatic approach
    "neo_soul_rnb": [
        _note(36, 0.0, 1.0, 85), _note(40, 1.0, 1.0, 80),
        _note(43, 2.0, 1.0, 85), _note(41, 3.0, 1.0, 80),
    ],
}

# Map genre_id -> bass pattern group
_GENRE_BASS_GROUP = {
    "house":        "house",
    "disco_funk":   "house",
    "lo_fi":        "house",
    "techno":       "techno",
    "drum_and_bass": "techno",
    "hip_hop_trap": "hiphop",
    "dubstep":      "dubstep",
    "trance":       "trance",
    "synthwave":    "trance",
    "future_bass":  "trance",
    "ambient":      "trance",
    "neo_soul_rnb": "neo_soul_rnb",
}

# Map genre_id -> drum pattern group (None = no drums)
_GENRE_DRUM_GROUP = {
    "house":        "house",
    "disco_funk":   "house",
    "lo_fi":        "house",
    "techno":       "techno",
    "drum_and_bass": "techno",
    "hip_hop_trap": "hiphop",
    "dubstep":      "dubstep",
    "trance":       "trance",
    "synthwave":    "trance",
    "future_bass":  "trance",
    "ambient":      None,
    "neo_soul_rnb": "neo_soul_rnb",
}

# ---------------------------------------------------------------------------
# Genre params: tempo midpoint, scale, instrument hints (D-05/D-08)
# ---------------------------------------------------------------------------

_GENRE_PARAMS = {
    "house":        {"bass": "Analog",    "harmony": "Wavetable", "melody": "Operator"},
    "techno":       {"bass": "Analog",    "harmony": "Wavetable", "melody": "Operator"},
    "ambient":      {"bass": "Analog",    "harmony": "Drift",     "melody": "Operator"},
    "hip_hop_trap": {"bass": "Wavetable", "harmony": "Wavetable", "melody": "Operator"},
    "drum_and_bass": {"bass": "Analog",   "harmony": "Wavetable", "melody": "Operator"},
    "dubstep":      {"bass": "Analog",    "harmony": "Wavetable", "melody": "Operator"},
    "trance":       {"bass": "Analog",    "harmony": "Wavetable", "melody": "Operator"},
    "synthwave":    {"bass": "Analog",    "harmony": "Wavetable", "melody": "Wavetable"},
    "future_bass":  {"bass": "Analog",    "harmony": "Wavetable", "melody": "Operator"},
    "lo_fi":        {"bass": "Wavetable", "harmony": "Wavetable", "melody": "Operator"},
    "neo_soul_rnb": {"bass": "Analog",    "harmony": "Wavetable", "melody": "Operator"},
    "disco_funk":   {"bass": "Analog",    "harmony": "Wavetable", "melody": "Operator"},
}

# ---------------------------------------------------------------------------
# Helper: build ExecutionStep dict
# ---------------------------------------------------------------------------

def _step(step_number, description, tool_name, suggested_args, phase, depends_on_step=None):
    # Omit depends_on_step when None to minimize tokens
    d = {
        "step_number": step_number,
        "tool_name": tool_name,
        "description": description,
        "suggested_args": suggested_args,
        "phase": phase,
    }
    if depends_on_step is not None:
        d["depends_on_step"] = depends_on_step
    return d


# ---------------------------------------------------------------------------
# Step builders per phase type
# ---------------------------------------------------------------------------

def _build_setup_steps(genre_id, blueprint):
    bpm_range = blueprint.get("bpm_range", [120, 130])
    tempo = (bpm_range[0] + bpm_range[1]) // 2
    scales = blueprint.get("harmony", {}).get("scales", ["natural_minor"])
    scale_name = scales[0].replace("_", " ").title() if scales else "Natural Minor"
    pt = "setup"
    return [
        _step(1, f"Set tempo to {tempo} BPM ({genre_id} midpoint)",
              "set_tempo", {"tempo": tempo}, pt),
        _step(2, f"Set scale to {scale_name}, root C",
              "set_scale", {"root_note": 0, "scale_name": scale_name}, pt, 1),
        _step(3, "Verify empty session",
              "get_arrangement_overview", {}, pt, 2),
        _step(4, "Scaffold arrangement (Intro 8 bars, Main 16 bars, Outro 8 bars)",
              "scaffold_arrangement", {
                  "plan": {
                      "genre": genre_id,
                      "sections": [
                          {"name": "Intro", "bars": 8},
                          {"name": "Main", "bars": 16},
                          {"name": "Outro", "bars": 8},
                      ],
                  }
              }, pt, 3),
        _step(5, "Verify scaffold applied",
              "get_arrangement_overview", {}, pt, 4),
        _step(6, "Check empty tracks",
              "get_arrangement_progress", {}, pt, 5),
    ]



# Sentinel hints removed — the "<track_index>" / "<clip_index>" values in
# suggested_args already signal that Claude must resolve them at call time.


def _build_drums_steps(genre_id, pattern, section_name):
    pt = "drums"
    kick_clap_notes = pattern["kick_clap"]
    hihat_notes = pattern["hihat"]
    clap_pitch = pattern.get("clap_pitch", 39)
    clap_label = "clap" if clap_pitch == 39 else "snare"
    has_clap = any(n["pitch"] != 36 for n in kick_clap_notes)
    beat_desc = f"kick+{clap_label}" if has_clap else "kick"

    if section_name:
        clip_step = _step(4,
            f"Arrangement clip for Drums in '{section_name}'",
            "create_arrangement_midi_clip",
            {"track_index": "<track_index>", "start_time": "<section_start_beat>", "length": "<section_length_beats>"},
            pt, 3)
    else:
        clip_step = _step(4,
            f"Session clip for Drums (4 bars)",
            "create_clip",
            {"track_index": "<track_index>", "clip_index": "<clip_index>", "length": 4.0},
            pt, 3)

    steps = [
        _step(1, "Create Drums MIDI track",
              "create_midi_track", {"index": -1}, pt),
        _step(2, f"Name track 'Drums'",
              "set_track_name", {"track_index": "<track_index>", "name": "Drums"}, pt, 1),
        _step(3, f"Load Drum Rack",
              "load_instrument_or_effect", {"track_index": "<track_index>", "instrument_name": "Drum Rack"}, pt, 2),
        clip_step,
        _step(5, f"Add {beat_desc} notes",
              "add_notes_to_clip",
              {"track_index": "<track_index>", "clip_index": "<clip_index>", "notes": kick_clap_notes},
              pt, 4),
        _step(6, f"Add hi-hat notes (p42)",
              "add_notes_to_clip",
              {"track_index": "<track_index>", "clip_index": "<clip_index>", "notes": hihat_notes},
              pt, 5),
        _step(7, "Quantize Drums clip",
              "quantize_notes",
              {"track_index": "<track_index>", "clip_index": "<clip_index>"},
              pt, 6),
    ]
    return steps


def _build_bass_steps(genre_id, instruments, section_name):
    pt = "bass"
    bass_instr = instruments.get("bass", "Analog")
    bass_group = _GENRE_BASS_GROUP.get(genre_id, "house")
    bass_notes = _BASS_PATTERNS[bass_group]

    if section_name:
        clip_step = _step(4,
            f"Arrangement clip for Bass in '{section_name}'",
            "create_arrangement_midi_clip",
            {"track_index": "<track_index>", "start_time": "<section_start_beat>", "length": "<section_length_beats>"},
            pt, 3)
    else:
        clip_step = _step(4,
            f"Session clip for Bass (4 bars)",
            "create_clip",
            {"track_index": "<track_index>", "clip_index": "<clip_index>", "length": 4.0},
            pt, 3)

    return [
        _step(1, "Create Bass MIDI track",
              "create_midi_track", {"index": -1}, pt),
        _step(2, f"Name track 'Bass'",
              "set_track_name", {"track_index": "<track_index>", "name": "Bass"}, pt, 1),
        _step(3, f"Load {bass_instr} on Bass track",
              "load_instrument_or_effect", {"track_index": "<track_index>", "instrument_name": bass_instr}, pt, 2),
        clip_step,
        _step(5, f"Add bass line notes",
              "add_notes_to_clip",
              {"track_index": "<track_index>", "clip_index": "<clip_index>", "notes": bass_notes},
              pt, 4),
        _step(6, f"Set Bass volume to 0.85",
              "set_track_volume",
              {"track_index": "<track_index>", "volume": 0.85},
              pt, 5),
    ]


def _build_harmony_steps(genre_id, instruments, section_name):
    pt = "harmony"
    harmony_instr = instruments.get("harmony", "Wavetable")
    chord_notes = [
        _note(48, 0.0, 2.0, 80), _note(52, 0.0, 2.0, 75), _note(55, 0.0, 2.0, 70),
        _note(50, 2.0, 2.0, 80), _note(53, 2.0, 2.0, 75), _note(57, 2.0, 2.0, 70),
    ]

    if section_name:
        clip_step = _step(4,
            f"Arrangement clip for Chords in '{section_name}'",
            "create_arrangement_midi_clip",
            {"track_index": "<track_index>", "start_time": "<section_start_beat>", "length": "<section_length_beats>"},
            pt, 3)
    else:
        clip_step = _step(4,
            f"Session clip for Chords (8 bars)",
            "create_clip",
            {"track_index": "<track_index>", "clip_index": "<clip_index>", "length": 8.0},
            pt, 3)

    return [
        _step(1, "Create Chords MIDI track",
              "create_midi_track", {"index": -1}, pt),
        _step(2, f"Name track 'Chords'",
              "set_track_name", {"track_index": "<track_index>", "name": "Chords"}, pt, 1),
        _step(3, f"Load {harmony_instr} on Chords track",
              "load_instrument_or_effect", {"track_index": "<track_index>", "instrument_name": harmony_instr}, pt, 2),
        clip_step,
        _step(5, f"Add 2-chord loop notes",
              "add_notes_to_clip",
              {"track_index": "<track_index>", "clip_index": "<clip_index>", "notes": chord_notes},
              pt, 4),
        _step(6, f"Set Chords volume to 0.75",
              "set_track_volume",
              {"track_index": "<track_index>", "volume": 0.75},
              pt, 5),
    ]


def _build_melody_steps(genre_id, instruments, section_name):
    pt = "melody"
    melody_instr = instruments.get("melody", "Operator")
    melody_notes = [
        _note(60, 0.0, 0.5, 90), _note(62, 0.5, 0.5, 85),
        _note(64, 1.0, 1.0, 95), _note(62, 2.0, 0.5, 85),
        _note(60, 2.5, 1.5, 90),
    ]

    if section_name:
        clip_step = _step(4,
            f"Arrangement clip for Lead in '{section_name}'",
            "create_arrangement_midi_clip",
            {"track_index": "<track_index>", "start_time": "<section_start_beat>", "length": "<section_length_beats>"},
            pt, 3)
    else:
        clip_step = _step(4,
            f"Session clip for Lead (8 bars)",
            "create_clip",
            {"track_index": "<track_index>", "clip_index": "<clip_index>", "length": 8.0},
            pt, 3)

    return [
        _step(1, "Create Lead MIDI track",
              "create_midi_track", {"index": -1}, pt),
        _step(2, f"Name track 'Lead'",
              "set_track_name", {"track_index": "<track_index>", "name": "Lead"}, pt, 1),
        _step(3, f"Load {melody_instr} on Lead track",
              "load_instrument_or_effect", {"track_index": "<track_index>", "instrument_name": melody_instr}, pt, 2),
        clip_step,
        _step(5, f"Add melodic phrase notes",
              "add_notes_to_clip",
              {"track_index": "<track_index>", "clip_index": "<clip_index>", "notes": melody_notes},
              pt, 4),
    ]


def _build_sound_design_steps(genre_id):
    pt = "sound_design"
    sn = "Replace <synth_track_index> with actual index from get_all_tracks()"
    return [
        _step(1, f"Load Auto Filter on synth track. {sn}",
              "load_instrument_or_effect",
              {"track_index": "<synth_track_index>", "instrument_name": "Auto Filter"},
              pt),
        _step(2, f"Set Auto Filter Frequency to 0.6. {sn}",
              "set_device_parameter",
              {"track_index": "<synth_track_index>", "device_index": 0, "parameter_name": "Frequency", "value": 0.6},
              pt, 1),
        _step(3, f"Load Reverb on synth track. {sn}",
              "load_instrument_or_effect",
              {"track_index": "<synth_track_index>", "instrument_name": "Reverb"},
              pt, 2),
        _step(4, f"Set Reverb Dry/Wet to 0.3. {sn}",
              "set_device_parameter",
              {"track_index": "<synth_track_index>", "device_index": 1, "parameter_name": "Dry/Wet", "value": 0.3},
              pt, 3),
    ]


def _build_arrangement_steps(genre_id, section_name):
    pt = "arrangement"
    sn = section_name or "<section_name>"
    return [
        _step(1, "Get arrangement overview",
              "get_arrangement_overview", {}, pt),
        _step(2, "Check arrangement progress",
              "get_arrangement_progress", {}, pt, 1),
        _step(3, f"Evaluate session for {genre_id}",
              "evaluate_session", {"genre": genre_id}, pt, 2),
        _step(4, f"Get section checklist for '{sn}'",
              "get_section_checklist",
              {"plan": {"genre": genre_id, "sections": []}, "section_name": sn},
              pt, 3),
        # Non-callable placeholder — filtered by next_actions before returning to Claude
        _step(5, "Review evaluate_session output and apply each item in top_fixes",
              "\u2014", {}, pt, 4),
    ]


def _build_mix_steps(genre_id, blueprint):
    pt = "mix"
    roles = blueprint.get("instrumentation", {}).get("roles", [])[:3]
    if not roles:
        roles = ["kick", "bass", "pad"]

    steps = []
    for i, role in enumerate(roles):
        steps.append(_step(
            i + 1,
            f"Apply mix recipe for {role}. Replace <{role}_track_index> with actual index from get_all_tracks().",
            "apply_mix_recipe",
            {"track_index": f"<{role}_track_index>", "role": role, "genre": genre_id},
            pt,
            i if i > 0 else None,
        ))

    n = len(steps)
    steps.append(_step(n + 1, "Check gain staging",
                       "check_gain_staging", {}, pt, n))
    steps.append(_step(n + 2, f"Suggest mix adjustments for {genre_id}",
                       "suggest_mix_adjustments", {"genre": genre_id}, pt, n + 1))
    return steps


def _build_master_steps(genre_id):
    pt = "master"
    return [
        _step(1, f"Apply master bus chain for {genre_id}",
              "apply_master_recipe", {"genre": genre_id}, pt),
        _step(2, f"Evaluate session after mastering",
              "evaluate_session", {"genre": genre_id}, pt, 1),
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_execution_plan(phase_name: str, genre: str,
                       section_name: str = None, context: dict = None) -> dict:
    """Return a PhaseChecklist for the given phase_name and genre.

    Args:
        phase_name: Phase type slug (setup/drums/bass/harmony/melody/
                    sound_design/arrangement/mix/master).
        genre: Genre id or alias (e.g. "house", "techno").
        section_name: Optional arrangement section name. When given, note-writing
                      steps use create_arrangement_midi_clip with sentinel positions.
        context: Optional override dict with keys: instrument, tempo, scale, root_note.

    Returns:
        PhaseChecklist dict or {"error": "..."} on unknown genre or invalid phase.
    """
    # Resolve genre
    resolved = resolve_alias(genre)
    if resolved is None:
        return {"error": f"Unknown genre '{genre}'. Use list_genre_blueprints() to see available genres."}
    genre_id = resolved["genre_id"]

    # Check ambient drums
    if phase_name == "drums" and genre_id == "ambient":
        return {"error": "No drums phase in ambient agenda"}

    blueprint = get_blueprint(genre_id)
    if blueprint is None:
        return {"error": f"No blueprint found for genre '{genre_id}'."}

    instruments = _GENRE_PARAMS.get(genre_id, {
        "bass": "Analog", "harmony": "Wavetable", "melody": "Operator"
    })

    # Apply context overrides
    if context:
        if "instrument" in context:
            instruments = dict(instruments)
            instruments[phase_name] = context["instrument"]

    # Build steps per phase
    phase_name_lower = phase_name.lower()
    if phase_name_lower == "setup":
        steps = _build_setup_steps(genre_id, blueprint)
    elif phase_name_lower == "drums":
        drum_group = _GENRE_DRUM_GROUP.get(genre_id, "house")
        if drum_group is None:
            return {"error": f"No drums phase in {genre_id} agenda"}
        pattern = _DRUM_PATTERNS[drum_group]
        steps = _build_drums_steps(genre_id, pattern, section_name)
    elif phase_name_lower == "bass":
        steps = _build_bass_steps(genre_id, instruments, section_name)
    elif phase_name_lower == "harmony":
        steps = _build_harmony_steps(genre_id, instruments, section_name)
    elif phase_name_lower == "melody":
        steps = _build_melody_steps(genre_id, instruments, section_name)
    elif phase_name_lower == "sound_design":
        steps = _build_sound_design_steps(genre_id)
    elif phase_name_lower == "arrangement":
        steps = _build_arrangement_steps(genre_id, section_name)
    elif phase_name_lower == "mix":
        steps = _build_mix_steps(genre_id, blueprint)
    elif phase_name_lower == "master":
        steps = _build_master_steps(genre_id)
    else:
        return {"error": f"Unknown phase '{phase_name}'. Valid phases: setup, drums, bass, harmony, melody, sound_design, arrangement, mix, master"}

    # Re-number steps sequentially (some builders use local numbering)
    for i, step in enumerate(steps):
        step["step_number"] = i + 1

    total = len(steps)
    # estimated_tool_calls excludes description-only steps (tool_name == "—")
    tool_calls = sum(1 for s in steps if s["tool_name"] != "—")

    return PhaseChecklist(
        phase_name=phase_name_lower,
        genre=genre_id,
        section=section_name,
        steps=steps,
        total_steps=total,
        estimated_tool_calls=tool_calls,
    )
