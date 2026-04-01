# Phase 48 Context: Production Agenda Schema and Genre Phase Catalog

**Phase:** 48 — Production Agenda Schema and Genre Phase Catalog
**Milestone:** v1.9 Orchestration/Agent Loop
**Requirements:** AGND-01, AGND-02
**Date:** 2026-03-31
**Mode:** --auto (no interactive questioning)

## Goal

`get_production_agenda(genre, brief?)` — returns an ordered `ProductionAgenda`
with genre-appropriate phase list; each `ProductionPhase` names the goal, type,
roles involved, and estimated step count. No execution or checkpoint logic yet.

## Codebase Scouting

### What exists and will be reused

| Asset | Location | Used for |
|-------|----------|----------|
| Genre catalog + list_genres() | `MCP_Server/genres/catalog.py` | Enumerate all 12 genre IDs for catalog |
| `resolve_alias()` | `MCP_Server/genres/catalog.py:30` | Normalize genre arg before lookup |
| Genre role lists | `MCP_Server/genres/*.py` GENRE["instrumentation"]["roles"] | Populate `roles` field per phase |
| `ProductionBrief` TypedDict | `MCP_Server/prompt/schema.py` | Type for optional `brief` param |
| `_derive_energy_level` | `MCP_Server/prompt/deriver.py` | Inspect brief energy_level for ordering override |
| TypedDict pattern | `MCP_Server/refinement/schema.py` | Follow same style: Optional, no .asdict() |
| Tool registration pattern | `MCP_Server/tools/refinement.py` | @mcp.tool() + json.dumps + ctx: Context |
| `tools/__init__.py` | `MCP_Server/tools/__init__.py` | Add `orchestration` import |
| `pyproject.toml` packages list | `pyproject.toml` | Add `MCP_Server.orchestration` |

### Package already exists for v1.8 refinement — same structure for orchestration

`MCP_Server/refinement/` has `__init__.py` + `schema.py` + `interpreter.py` + `lexicon.py`.
`MCP_Server/orchestration/` will follow identical layout: `__init__.py` + `schema.py` + `agenda.py`.
Tool wiring lives in `MCP_Server/tools/orchestration.py`.

## Locked Decisions

### D-01: Package layout

```
MCP_Server/orchestration/
  __init__.py          # exposes get_production_agenda, AGENDA_CATALOG
  schema.py            # all TypedDicts: ProductionPhase, ProductionAgenda,
                       # ExecutionStep, PhaseChecklist, ProductionCheckpoint
                       # (all 5 schemas defined here even if used in later phases)
  agenda.py            # AGENDA_CATALOG dict + get_agenda(genre, brief) logic

MCP_Server/tools/
  orchestration.py     # get_production_agenda MCP tool (Phase 48 only)
```

All TypedDicts defined in `schema.py` up front — avoids import ordering issues
in Phases 49-51 when they import from the same schema module.

### D-02: TypedDict schemas (all phases)

Defined in `MCP_Server/orchestration/schema.py`:

```python
from typing import Literal, Optional, TypedDict

PhaseType = Literal[
    "setup", "drums", "bass", "harmony", "melody",
    "sound_design", "arrangement", "mix", "master"
]

class ProductionPhase(TypedDict):
    name: str                    # human-readable (e.g., "Drum Programming")
    phase_id: str                # slug (e.g., "drums") matches phase_type
    phase_type: str              # one of PhaseType literals
    goal: str                    # one sentence: what this phase produces
    roles: list                  # list[str] from genre instrumentation.roles
    estimated_steps: int         # typical tool call count for this phase
    depends_on: list             # list[str] of phase_ids that must precede this

class ProductionAgenda(TypedDict):
    genre: str
    phases: list                 # list[ProductionPhase]
    total_estimated_steps: int   # sum of all phase estimated_steps

# Phase 49 schemas (defined here, implemented in Phase 49)
class ExecutionStep(TypedDict):
    step_number: int
    description: str             # plain English action
    tool_name: str               # exact registered MCP tool name
    suggested_args: dict         # {param: value} ready to pass to tool
    depends_on_step: Optional[int]
    phase: str                   # phase_id this step belongs to

class PhaseChecklist(TypedDict):
    phase_name: str
    genre: str
    section: Optional[str]
    steps: list                  # list[ExecutionStep]
    total_steps: int
    estimated_tool_calls: int

# Phase 50 schemas (defined here, implemented in Phase 50)
class SessionStats(TypedDict):
    track_count: int
    tracks_with_instruments: int
    tracks_with_clips: int
    has_mix_applied: bool
    has_master_applied: bool

class ProductionCheckpoint(TypedDict):
    genre: Optional[str]
    completed_phases: list       # list[str] of phase_ids inferred complete
    active_phase: Optional[str]  # phase_id currently in progress
    active_phase_progress: float # 0.0–1.0
    pending_steps: list          # list[str] human-readable pending items
    session_stats: dict          # SessionStats
    next_phase: Optional[str]    # phase_id after active_phase
    resume_hint: str             # single sentence: what to do next
```

### D-03: AGENDA_CATALOG — 12 genre phase orderings

Pure dict in `agenda.py`. Key = genre_id, value = ordered list of phase dicts.

**Phase ordering rules:**
- Every genre starts with `setup` and ends with `mix → master`
- Rhythmic-first genres (techno, dnb, dubstep, house, disco_funk): drums → bass before harmony
- Melody-forward genres (trance, synthwave, future_bass): harmony → melody elevated; sound_design before arrangement
- Vocal/soul genres (neo_soul_rnb, hip_hop_trap, lo_fi): harmony prominent; bass after drums
- Texture genres (ambient): no drums phase; harmony ("Pads") → sound_design ("Textures") → arrangement

Full 12-genre phase ordering:

| Genre | Phase order (phase_ids) |
|-------|------------------------|
| house | setup→drums→bass→harmony→melody→arrangement→sound_design→mix→master |
| techno | setup→drums→bass→sound_design→arrangement→mix→master |
| ambient | setup→harmony→sound_design→arrangement→mix→master |
| hip_hop_trap | setup→drums→bass→harmony→melody→arrangement→mix→master |
| drum_and_bass | setup→drums→bass→melody→arrangement→sound_design→mix→master |
| dubstep | setup→drums→bass→sound_design→melody→arrangement→mix→master |
| trance | setup→drums→bass→harmony→melody→sound_design→arrangement→mix→master |
| synthwave | setup→drums→bass→harmony→melody→sound_design→arrangement→mix→master |
| future_bass | setup→drums→harmony→bass→melody→sound_design→arrangement→mix→master |
| lo_fi | setup→drums→bass→harmony→melody→arrangement→mix→master |
| neo_soul_rnb | setup→harmony→bass→drums→melody→arrangement→sound_design→mix→master |
| disco_funk | setup→drums→bass→harmony→melody→arrangement→mix→master |

Ambient uses phase_type="harmony" with name="Pads / Chords" and
phase_type="sound_design" with name="Textures & Drones" — same types, genre-flavored names.

### D-04: Estimated step counts per phase_type

Used to compute `estimated_steps` for each `ProductionPhase`:

| phase_type | estimated_steps | Rationale |
|------------|----------------|-----------|
| setup | 8 | set_tempo + set_scale + scaffold_arrangement + 5 track creates |
| drums | 12 | create track + load DR + 4 note-writing calls + quantize + sends |
| bass | 8 | create track + load instrument + bass line + octave + rhythm + sends |
| harmony | 10 | create track + load + chord progression + voicing + 3 sections + sends |
| melody | 8 | create track + load + main melody + variation + sends |
| sound_design | 10 | 2-3 tracks × (load device + set 3 params) |
| arrangement | 6 | variation per section (copy + modify notes × 2-3 sections) |
| mix | 8 | apply_mix_recipe + check_gain + suggest_adjustments + master |
| master | 3 | apply_master_recipe |

### D-05: Phase roles are pulled from genre blueprint

For each phase, `roles` is drawn from the genre's `instrumentation.roles` list
filtered to the phase type:
- drums: roles matching ["kick","snare","hi-hats","clap","percussion","808_bass"]
- bass: roles matching ["bass","808_bass","sub"]
- harmony: roles matching ["pad","chord","stab","strings","piano","keys","guitar"]
- melody: roles matching ["lead","melody","vocal","vocal_chop","keys"]
- sound_design: all remaining roles not in drums/bass/harmony/melody
- setup/arrangement/mix/master: use full genre roles list (abbreviated to first 5)

If a genre doesn't have a drums role list entry, that phase is omitted from its agenda.
(Ambient has no drums → no drums phase.)

### D-06: Brief override — energy_level shifts phase order

When `brief` dict is provided and `brief["energy_level"] >= 7`:
- Move `drums` to position 1 (immediately after setup) if not already there
- No other reordering

When `brief["primary_genre"]` is set:
- It overrides the `genre` argument for catalog lookup
- The `genre` arg is used only as fallback if primary_genre is not in AGENDA_CATALOG

Brief must be a plain dict (ProductionBrief shape); no type enforcement at runtime.
Invalid/partial briefs are silently ignored (no exceptions from brief parsing).

### D-07: `get_production_agenda` MCP tool signature

```python
async def get_production_agenda(ctx: Context, genre: str, brief: str = None) -> str:
```

- `genre`: genre id or alias (resolved via `resolve_alias`)
- `brief`: optional JSON string of a `ProductionBrief` dict (not a dict directly — MCP tools receive strings)
- Returns: `json.dumps(ProductionAgenda)` or JSON error string on unknown genre
- Unknown genre → `{"error": "Unknown genre 'foo'. Use list_genre_blueprints() to see available genres."}`

### D-08: Token budget enforcement

Target: total JSON output ≤400 tokens.
`goal` field for each phase: max 12 words (one sentence fragment).
`roles` list: max 6 roles per phase.
If a genre's agenda exceeds 400 tokens, truncate `roles` to 4 and shorten `goal` strings.
No token counting in runtime code — sizes validated in tests against hardcoded limits.

### D-09: pyproject.toml update

Add `"MCP_Server.orchestration"` to the `packages` list alongside existing entries.

## Implementation Order

1. **schema.py** — all 5 TypedDicts (ProductionPhase, ProductionAgenda, ExecutionStep, PhaseChecklist, ProductionCheckpoint + SessionStats)
2. **agenda.py** — `AGENDA_CATALOG` dict for 12 genres + `get_agenda(genre, brief)` function
3. **`__init__.py`** — expose `get_agenda`, `AGENDA_CATALOG`
4. **tools/orchestration.py** — `get_production_agenda` MCP tool with json.dumps return
5. **tools/__init__.py** — add `orchestration` to imports
6. **pyproject.toml** — add `MCP_Server.orchestration`
7. **Tests** — `tests/test_production_agenda.py` (all 5 success criteria)

## Test Coverage

| Test | What it verifies |
|------|-----------------|
| `test_techno_agenda_phase_order` | techno returns setup→drums→bass→sound_design→arrangement→mix→master |
| `test_ambient_no_drums_phase` | ambient agenda has no phase with phase_type="drums" |
| `test_brief_energy_override` | brief with energy_level=8 moves drums to position 1 |
| `test_brief_genre_override` | brief primary_genre overrides genre arg |
| `test_unknown_genre_error` | returns error dict, not exception |
| `test_total_steps_sum` | total_estimated_steps == sum of phase estimated_steps |
| `test_json_output_under_400_tokens` | serialized JSON ≤ 400 tokens for all 12 genres |
| `test_roles_from_blueprint` | house drums phase includes "kick","snare","hi-hats" |

## Out of Scope for Phase 48

- Execution step generation (Phase 49)
- Checkpoint reading from Ableton (Phase 50)
- Next-action recommender (Phase 51)
- Adaptive agenda modification
- Parallel phase support
