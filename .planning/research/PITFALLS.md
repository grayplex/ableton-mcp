# Domain Pitfalls: v1.2 Genre/Style Blueprints

**Domain:** Genre blueprint system for electronic music production MCP server
**Researched:** 2026-03-25
**Confidence:** HIGH

## Critical Pitfalls

Mistakes that cause rewrites or major architectural issues.

### Pitfall 1: Blueprint-Theory Circular Dependencies

**What goes wrong:** Blueprint modules import theory functions to pre-compute MIDI data or validate chord names at import time. Theory modules later need blueprint data for genre-aware suggestions. Circular import breaks both systems.

**Why it happens:** Natural desire to "pre-resolve" blueprint harmony data into MIDI at load time for convenience.

**Consequences:** `ImportError` at startup. Or worse: subtle load-order dependency where blueprints must import after theory, making the import chain fragile.

**Prevention:** Blueprints store **string names only** (e.g., `"chord_types": ["min7", "dom9"]`). Only the `get_genre_palette` tool (in `tools/blueprints.py`) bridges the gap at runtime by calling theory functions. Blueprint library modules never import from theory library modules.

**Detection:** Any `from MCP_Server.theory import ...` in `blueprints/*.py` is a red flag.

### Pitfall 2: Overly Verbose Blueprints That Flood Context

**What goes wrong:** Each blueprint returns 3000+ tokens of detailed text. Claude calls `get_genre_blueprint` and loses significant context window to reference data, leaving less room for reasoning about the actual production task.

**Why it happens:** Enthusiasm for comprehensive documentation. Every section gets paragraphs of explanation.

**Consequences:** Degraded Claude performance on complex multi-step production tasks. Context exhaustion on long conversations.

**Prevention:**
1. Section filtering (`sections=["harmony"]`) so Claude requests only what it needs.
2. Keep blueprint data concise -- structured dicts with terse values, not prose paragraphs.
3. Use the `notes` field sparingly (one sentence max per section).
4. Target 800-1200 tokens for a full blueprint, 200-400 for a single section.

**Detection:** Measure token count of `json.dumps(blueprint)` during testing. Flag any blueprint over 1500 tokens.

### Pitfall 3: Genre Data Inaccuracy

**What goes wrong:** Blueprint contains incorrect BPM ranges, wrong chord conventions, or misleading mixing advice. Claude confidently follows the blueprint and produces genre-inappropriate music.

**Why it happens:** Genre conventions are nuanced and author-dependent. Easy to over-generalize or conflate subgenres. Research from one source may not represent consensus.

**Consequences:** Users lose trust in the system. "This doesn't sound like techno" is a hard error to diagnose because the data, not the code, is wrong.

**Prevention:**
1. Cross-reference multiple sources for each genre (producer forums, academic analyses, production tutorials).
2. Use BPM ranges (not single values) and preference lists (not single choices).
3. Include subgenres to avoid over-generalizing the parent genre.
4. Review blueprints with actual producers if possible.

**Detection:** Include a `sources` or `references` field in each blueprint for traceability.

## Moderate Pitfalls

### Pitfall 4: Subgenre Merge Producing Nonsense

**What goes wrong:** Deep dict merging causes unexpected results. For example, a subgenre overrides `harmony.chord_types` but not `harmony.scales`, producing an inconsistent harmony section that mixes parent and child conventions incorrectly.

**Prevention:** Use shallow merge only -- subgenre keys replace parent keys entirely at the top level. If a subgenre needs different harmony, it provides the complete `harmony` dict, not a partial override. Document this clearly in schema.py.

### Pitfall 5: Inconsistent Schema Across Genres

**What goes wrong:** House blueprint has `instrumentation.drums.kick` but techno blueprint uses `instrumentation.drums.bass_drum`. Genre data files drift in structure over time, causing tools to fail on some genres but not others.

**Prevention:** Define the canonical schema in `schema.py` with a validation function. Run validation at import time (not just in tests). Every genre module is validated when the catalog loads. Test that every genre passes schema validation.

### Pitfall 6: Palette Tool Failures on Edge Cases

**What goes wrong:** `get_genre_palette` calls `build_chord(key, quality)` with a chord quality from the blueprint, but the theory engine doesn't support that quality name. Tool returns an error instead of useful data.

**Prevention:**
1. Constrain blueprint `chord_types` to qualities the theory engine actually supports (currently 26 qualities in `chords.py`).
2. Use try/except in the palette tool -- skip unsupported qualities gracefully rather than failing entirely.
3. Add a test that validates every chord_type and scale name in every blueprint against the theory engine's supported types.

### Pitfall 7: Tool Description Too Vague for Claude

**What goes wrong:** Claude never calls `get_genre_blueprint` because the tool description doesn't clearly signal when it's useful. The tool exists but is effectively invisible.

**Prevention:** Write tool descriptions that explicitly state the trigger conditions: "Use this when producing music in a specific genre" and "Returns instrumentation, harmony, rhythm, arrangement, and mixing guidance." Include genre examples in the description.

## Minor Pitfalls

### Pitfall 8: Forgetting to Update tools/__init__.py

**What goes wrong:** Blueprint tools are defined but never registered because `tools/__init__.py` doesn't import the blueprints module.

**Prevention:** The very first phase should include updating `tools/__init__.py` and verifying tool registration. Add a test that checks `mcp._tool_manager._tools` contains the blueprint tools.

### Pitfall 9: Genre Key Naming Inconsistency

**What goes wrong:** Blueprint uses `"drum_and_bass"` but user asks Claude for "dnb" or "DnB". Claude can't map the user's language to the genre key.

**Prevention:** Add an `aliases` field to each blueprint: `"aliases": ["dnb", "d&b", "jungle"]`. The catalog lookup function checks aliases in addition to the primary key.

### Pitfall 10: Missing pyproject.toml Package Registration

**What goes wrong:** Blueprints work in development (running from source) but fail when installed as a package because `MCP_Server.blueprints` isn't in the packages list.

**Prevention:** Add both `MCP_Server.blueprints` and `MCP_Server.blueprints.genres` to `[tool.setuptools] packages` in pyproject.toml. Test with `pip install -e .` after adding the package.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Schema definition | Over-engineering the schema (TypedDict, Pydantic, dataclasses) | Keep it simple: plain dicts with a validation function |
| First genre (house) | Spending too long perfecting one genre before validating the full pipeline | Get end-to-end working first (schema -> catalog -> tool -> test), then refine content |
| Content authoring (12 genres) | Schema drift between genres | Run schema validation in every test; catch drift immediately |
| Palette bridge tool | Assuming all blueprint chord/scale names exist in theory engine | Validate names at import; graceful fallback in palette tool |
| Integration | Import order issues between blueprints and theory | Blueprints never import theory; only tools/blueprints.py crosses the boundary |

## Sources

- Existing codebase analysis: theory engine patterns, tool registration patterns
- Production domain knowledge: genre convention complexity, subgenre nuances
- MCP protocol understanding: tool discoverability, context window management

---
*Pitfalls research for: v1.2 Genre/Style Blueprints*
*Researched: 2026-03-25*
