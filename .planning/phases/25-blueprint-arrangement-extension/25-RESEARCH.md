# Phase 25: Blueprint Arrangement Extension - Research

**Researched:** 2026-03-27
**Domain:** Genre blueprint schema extension + data authoring (pure Python dicts)
**Confidence:** HIGH

## Summary

Phase 25 extends the existing `ArrangementEntry` TypedDict in `schema.py` with three optional fields (`energy`, `roles`, `transition_in`) and populates those fields across all 12 genre blueprint files. The subgenre merge logic in `catalog.py` already performs shallow key-level merge, which means subgenres that override `arrangement` will need their own new-field data authored, while subgenres that inherit arrangement from the parent get the new fields for free.

This is a data-authoring-heavy phase with minimal code changes. The schema extension is a ~10-line change. The validator update is a ~15-line change. The bulk of the work is authoring musically accurate energy/roles/transition_in values for 89 base-genre sections plus 27 subgenre-overridden sections (4 subgenres override arrangement). Token budget analysis shows all genres remain well within the 1200-token ceiling after the extension.

**Primary recommendation:** Implement schema + validator first, then author house.py as the reference template, then extend the remaining 11 genres and 4 arrangement-overriding subgenres, then write new tests for the new fields. Keep existing tests completely untouched.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** New fields are added to `ArrangementEntry` TypedDict as optional (not required) -- keeps `validate_blueprint()` backward-compatible so existing test fixtures without the new fields still pass
- **D-02:** In all actual genre blueprints, every section is authored with the new fields (energy, roles, and transition_in where applicable) -- optional in schema, populated in practice
- **D-03:** Subgenres inherit energy/roles/transition_in from parent genre's matching section by name (default). Subgenres MAY optionally override on a per-section basis if their energy curve or roles differ meaningfully from the parent.
- **D-04:** The first section (typically "intro") omits `transition_in` entirely -- no key, no empty string, no null. Code downstream must handle absence gracefully. Also applies to any section that is structurally "the start."
- **D-05:** Per-section `roles` are a soft-constrained subset of `instrumentation.roles` -- convention only, not enforced by the validator. Role strings should match the genre's top-level instrumentation roles. Tests spot-check but do not fail on section-specific roles like "riser" or "fx_swell."
- **D-06:** Energy levels (1-10) model the section's energy curve: intro ~2-3, buildup ramps up, drop peaks at 8-10, breakdown drops to 3-5, outro fades to 2-3. Each genre's curve should reflect its actual energy arc.
- **D-07:** Per-section roles list the instrument roles ACTIVE in that section (not silent/absent ones).
- **D-08:** `transition_in` is a short descriptor phrase (e.g., "filter sweep + riser", "impact hit"). Should be actionable enough for Claude to use as a production instruction.

### Claude's Discretion
- Exact energy values per section per genre (follow D-06 guidance)
- Exact role lists per section (follow D-05 convention)
- Exact transition_in strings per section (follow D-08 guidance)
- How subgenre merge logic resolves inherited vs. overridden section data (catalog.py implementation detail)
- Whether TypedDict uses `total=False` on a subclass or `Optional` fields for the new keys

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ARNG-01 | User can retrieve per-section energy level (int 1-10) from genre blueprints | `energy` field added to `ArrangementEntry` TypedDict; populated in all 12 genre files; validator optionally checks type/range; `get_genre_blueprint` tool returns it automatically via `json.dumps(blueprint)` |
| ARNG-02 | User can retrieve per-section instrument roles list from genre blueprints | `roles` field (List[str]) added to `ArrangementEntry`; populated in all 12 genre files; role strings drawn from genre's `instrumentation.roles` (convention, not enforced) |
| ARNG-03 | User can retrieve per-section transition descriptor from genre blueprints | `transition_in` field (str) added to `ArrangementEntry`; populated in all sections except intro/first sections (D-04: absent, not empty); no tool changes needed |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python typing (TypedDict) | 3.10 stdlib | Schema definition | Already used throughout; `total=False` subclass pattern available in 3.10+ |

### Supporting
No external libraries needed. This phase is pure Python data authoring with no new dependencies.

## Architecture Patterns

### Recommended TypedDict Extension Pattern

The existing `ArrangementEntry` has `name: str` and `bars: int` as required fields. The extension should use TypedDict inheritance with `total=False` to make new fields optional:

```python
# Source: verified working on Python 3.10.5 (project runtime)
class _ArrangementEntryRequired(TypedDict):
    """Required fields for arrangement entries."""
    name: str
    bars: int

class ArrangementEntry(_ArrangementEntryRequired, total=False):
    """A single section in an arrangement.

    Required: name, bars
    Optional: energy, roles, transition_in (added in v1.3 Phase 25)
    """
    energy: int              # 1-10 energy level
    roles: List[str]         # Active instrument roles in this section
    transition_in: str       # How to transition into this section
```

This pattern:
- Preserves `name` and `bars` as required (existing validation passes)
- Makes `energy`, `roles`, `transition_in` optional at the type level
- The `_make_valid_blueprint()` test fixture has sections without new fields and continues to pass validation
- All actual genre blueprints populate the new fields per D-02

### Validator Extension Pattern

The existing `validate_blueprint()` checks `name` (str) and `bars` (int) on each section entry. The extension should add **optional** validation: if a new field is present, check its type and constraints; if absent, skip silently.

```python
# Inside validate_blueprint(), after the existing name/bars checks:
for i, entry in enumerate(data["arrangement"]["sections"]):
    # ... existing name/bars checks ...

    # Optional new fields (v1.3): validate type if present
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
```

### Subgenre Merge: No Changes Needed to catalog.py

The existing shallow merge in `catalog.py` (line 173) replaces top-level keys entirely:

```python
for key, value in sub_overrides.items():
    result[key] = value
```

When a subgenre overrides `arrangement`, it replaces the entire `arrangement` dict. This means:
- Subgenres that DO NOT override arrangement: inherit all new fields from parent automatically
- Subgenres that DO override arrangement: their `sections` entries must include the new fields

Per D-03, the merge is at the `arrangement` level (shallow), not at the per-section level. There is no need to implement per-section-name merge logic. If a subgenre overrides arrangement, it provides all its own section data including the new fields.

### Genre Files Affected

**12 base genres** (89 total sections to author):

| Genre | Sections | Section Names |
|-------|----------|---------------|
| house | 7 | intro, buildup, drop, breakdown, buildup2, drop2, outro |
| techno | 7 | intro, buildup, drop, breakdown, buildup2, drop2, outro |
| hip_hop_trap | 8 | intro, verse, hook, verse2, hook2, bridge, hook3, outro |
| ambient | 7 | intro, movement1, transition, movement2, transition2, movement3, outro |
| drum_and_bass | 7 | intro, buildup, drop, breakdown, buildup2, drop2, outro |
| dubstep | 7 | intro, buildup, drop, breakdown, buildup2, drop2, outro |
| trance | 7 | intro, buildup, climax, breakdown, buildup2, climax2, outro |
| neo_soul_rnb | 10 | intro, verse, prechorus, chorus, verse2, prechorus2, chorus2, bridge, chorus3, outro |
| synthwave | 8 | intro, verse, chorus, verse2, chorus2, bridge, chorus3, outro |
| lo_fi | 6 | intro, loop_a, loop_b, loop_a2, loop_b2, outro |
| future_bass | 7 | intro, buildup, drop, breakdown, buildup2, drop2, outro |
| disco_funk | 8 | intro, verse, chorus, verse2, chorus2, bridge, chorus3, outro |

**4 subgenres with arrangement overrides** (27 additional sections):

| Subgenre | Parent | Sections | Section Names |
|----------|--------|----------|---------------|
| progressive_house | house | 7 | intro, buildup, drop, breakdown, buildup2, drop2, outro |
| melodic (techno) | techno | 7 | intro, buildup, drop, breakdown, buildup2, drop2, outro |
| peaktime_driving (techno) | techno | 7 | intro, buildup, drop, breakdown, buildup2, drop2, outro |
| cinematic (ambient) | ambient | 6 | intro, theme, development, climax, resolution, outro |

**Total sections to author:** 89 (base) + 27 (subgenre overrides) = 116 sections

### Anti-Patterns to Avoid
- **Modifying existing test fixtures:** The `_make_valid_blueprint()` helper creates sections without new fields. Do NOT add new fields to it -- backward compatibility requires it to pass as-is.
- **Making new fields required in the validator:** Would break the 117 existing tests that use fixtures without the new fields.
- **Adding transition_in to intro sections:** D-04 explicitly forbids this. Intro/first sections should not have a `transition_in` key at all.
- **Empty roles lists:** Every section should have at least one active role. Even sparse sections (intro with just kick + hi-hats) should list those roles.
- **Generic energy curves:** D-06 requires genre-specific curves. Ambient should not have the same curve as dubstep.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TypedDict optional fields | Custom validation logic for optional keys | `total=False` subclass inheritance | Standard Python pattern, type-checker-friendly |
| Subgenre section inheritance | Custom per-section-name merge | Existing shallow merge in catalog.py | Already works -- subgenres that override arrangement replace the whole dict |

## Common Pitfalls

### Pitfall 1: Breaking the 117 Existing Tests
**What goes wrong:** Adding required fields to `ArrangementEntry` or to the validator causes test fixtures (which lack the new fields) to fail validation.
**Why it happens:** Conflating "all real blueprints have these fields" with "the schema requires these fields."
**How to avoid:** Use `total=False` on the TypedDict subclass. In the validator, only check new fields if they are present (if "energy" in entry).
**Warning signs:** Any test in `test_genres.py` failing after schema changes.

### Pitfall 2: Forgetting Subgenre Arrangement Overrides
**What goes wrong:** Base genre sections get new fields, but subgenres that override arrangement don't -- resulting in subgenre blueprints missing energy/roles/transition_in.
**Why it happens:** Only 4 of ~40 subgenres override arrangement, easy to miss.
**How to avoid:** Explicitly list the 4 subgenres: `progressive_house`, `melodic` (techno), `peaktime_driving` (techno), `cinematic` (ambient). Each must have the new fields authored in their arrangement override.
**Warning signs:** Subgenre blueprint returns sections without energy/roles/transition_in.

### Pitfall 3: Token Budget Overflow
**What goes wrong:** Adding verbose role lists and transition descriptions pushes a genre over the 1200-token ceiling.
**Why it happens:** test_genre_quality.py enforces a token budget per genre.
**How to avoid:** Rough analysis shows all genres stay under 750 tokens after the extension (current max is ~510). Keep role lists concise (4-6 items per section) and transition_in strings short (3-6 words).
**Warning signs:** `test_genre_quality.py::TestTokenBudget::test_all_genres_within_token_budget` failing. Note: this test requires `tiktoken` which is not currently installed -- must be installed or this test skipped during development.

### Pitfall 4: Inconsistent transition_in on Intro Sections
**What goes wrong:** Some intro sections get `transition_in: ""` or `transition_in: None` instead of omitting the key entirely.
**Why it happens:** Applying new fields uniformly to all sections without checking D-04.
**How to avoid:** For intro/first sections, do NOT include the `transition_in` key at all. Tests should verify absence, not empty string.
**Warning signs:** `"transition_in" in section` returns True for intro sections.

### Pitfall 5: tiktoken Not Installed
**What goes wrong:** `test_genre_quality.py` fails to collect because `tiktoken` is not installed in the current environment.
**Why it happens:** The quality test file imports tiktoken at module level.
**How to avoid:** Install tiktoken (`pip install tiktoken`) before running the full test suite, or note that the quality tests are a separate concern. The 117 tests in `test_genres.py` do not depend on tiktoken.
**Warning signs:** `ModuleNotFoundError: No module named 'tiktoken'` during test collection.

## Code Examples

### Example: House Genre Section with New Fields

```python
# Before (current)
{"name": "intro", "bars": 16}

# After (with new fields, D-04: no transition_in for intro)
{"name": "intro", "bars": 16, "energy": 2, "roles": ["kick", "hi-hats", "pad"]}

# After (non-intro section with transition_in)
{"name": "buildup", "bars": 8, "energy": 5, "roles": ["kick", "hi-hats", "clap", "bass", "pad", "fx"], "transition_in": "filter sweep + riser"}

# After (drop section -- peak energy)
{"name": "drop", "bars": 32, "energy": 9, "roles": ["kick", "bass", "hi-hats", "clap", "lead", "pad", "stab"], "transition_in": "impact hit + full drop"}
```

### Example: Subgenre with Arrangement Override (progressive_house)

```python
"progressive_house": {
    "name": "Progressive House",
    "bpm_range": [124, 132],
    "aliases": ["progressive house", "progressive", "prog house"],
    "harmony": { ... },
    "arrangement": {
        "sections": [
            {"name": "intro", "bars": 32, "energy": 2, "roles": ["pad", "percussion", "fx"]},
            {"name": "buildup", "bars": 16, "energy": 5, "roles": ["kick", "bass", "pad", "lead", "fx"], "transition_in": "gradual layering + filter open"},
            # ... etc
        ]
    },
},
```

### Example: New Test for Arrangement Extension

```python
class TestArrangementExtension:
    """ARNG-01/02/03: Arrangement data extension tests."""

    def test_house_sections_have_energy(self):
        bp = get_blueprint("house")
        for section in bp["arrangement"]["sections"]:
            assert "energy" in section, f"Section '{section['name']}' missing energy"
            assert 1 <= section["energy"] <= 10

    def test_house_sections_have_roles(self):
        bp = get_blueprint("house")
        for section in bp["arrangement"]["sections"]:
            assert "roles" in section, f"Section '{section['name']}' missing roles"
            assert isinstance(section["roles"], list)
            assert len(section["roles"]) > 0

    def test_house_intro_no_transition_in(self):
        """D-04: First section has no transition_in key."""
        bp = get_blueprint("house")
        intro = bp["arrangement"]["sections"][0]
        assert intro["name"] == "intro"
        assert "transition_in" not in intro

    def test_house_non_intro_have_transition_in(self):
        bp = get_blueprint("house")
        for section in bp["arrangement"]["sections"][1:]:
            assert "transition_in" in section, f"Section '{section['name']}' missing transition_in"
            assert isinstance(section["transition_in"], str)
            assert len(section["transition_in"]) > 0
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (installed, version available) |
| Config file | None (uses defaults) |
| Quick run command | `python -m pytest tests/test_genres.py -x -q` |
| Full suite command | `python -m pytest tests/test_genres.py tests/test_genre_quality.py -q` (requires tiktoken) |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ARNG-01 | Every section in every genre has energy (int 1-10) | unit | `python -m pytest tests/test_arrangement_extension.py::TestArrangementExtension -x` | Wave 0 |
| ARNG-02 | Every section has roles (non-empty list of strings) | unit | `python -m pytest tests/test_arrangement_extension.py::TestArrangementExtension -x` | Wave 0 |
| ARNG-03 | Non-intro sections have transition_in (string); intro sections lack it | unit | `python -m pytest tests/test_arrangement_extension.py::TestArrangementExtension -x` | Wave 0 |
| Backward compat | All 117 existing tests pass without modification | regression | `python -m pytest tests/test_genres.py -x -q` | Exists (117 tests) |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_genres.py tests/test_arrangement_extension.py -x -q`
- **Per wave merge:** `python -m pytest tests/test_genres.py tests/test_arrangement_extension.py -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_arrangement_extension.py` -- covers ARNG-01, ARNG-02, ARNG-03 across all 12 genres + 4 subgenre overrides
- [ ] Install tiktoken: `pip install tiktoken` -- if token budget tests needed during phase

## Open Questions

1. **tiktoken installation**
   - What we know: `test_genre_quality.py` requires tiktoken but it is not installed
   - What's unclear: Whether it should be installed as a dev dependency for this phase
   - Recommendation: Install it if token budget verification is desired; the quality tests are not blocking for this phase since the token budget analysis shows comfortable headroom

## Sources

### Primary (HIGH confidence)
- `MCP_Server/genres/schema.py` -- current ArrangementEntry TypedDict and validate_blueprint() logic
- `MCP_Server/genres/catalog.py` -- shallow merge logic for subgenres (lines 170-174)
- `MCP_Server/genres/house.py` -- canonical blueprint with 7 sections and 4 subgenres
- `tests/test_genres.py` -- 117 existing tests, _make_valid_blueprint() fixture
- `tests/test_genre_quality.py` -- token budget and theory cross-validation (8 tests)
- Python 3.10 typing docs -- TypedDict `total=False` inheritance verified on project runtime

### Secondary (MEDIUM confidence)
- Token budget estimates based on 4-chars-per-token heuristic (actual tiktoken not available). All genres are estimated at under 750 tokens post-extension against a 1200 ceiling, providing ~60% headroom.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- pure Python stdlib, no external dependencies
- Architecture: HIGH -- all code inspected, TypedDict pattern verified on project runtime
- Pitfalls: HIGH -- based on direct analysis of existing code, tests, and data
- Data authoring: MEDIUM -- energy values, role assignments, and transition strings are subjective musical decisions; guidelines from D-06/D-07/D-08 constrain but do not prescribe exact values

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable domain, no external dependencies)
