# Phase 37: Descriptor Taxonomy and Scoring Engine - Context

**Gathered:** 2026-03-31
**Mode:** auto (Claude selected recommended defaults)
**Status:** Ready for planning

<domain>
## Phase Boundary

Add `catalog.recommend(descriptor)` and `catalog.list_descriptors()` to the existing `MCP_Server/sounds/catalog.py`, and create `MCP_Server/tools/sounds.py` with the `list_sound_descriptors` MCP tool registered in `tools/__init__.py`. This phase wires descriptor strings to instrument rankings using weighted sum scoring over the 6 existing profiles. Phase 38 will add the remaining 2 MCP tools to the same sounds.py file.

</domain>

<decisions>
## Implementation Decisions

### Tokenization (D-01)
- **D-01:** Tokenize descriptor strings by splitting on whitespace after lowercasing and stripping punctuation. `"Warm Pad!"` → `["warm", "pad"]`. No stemming, no stop-word removal. Simple and predictable.

### Scoring Algorithm (D-02)
- **D-02:** Weighted sum scoring: for each token in the tokenized query, look it up in each instrument's `descriptor_affinities["role"]` and `descriptor_affinities["character"]` dicts. Sum all matched weights (a token can match in both role and character axes -- both contribute). Rank all instruments by total score descending. If a token is not found in any profile, its contribution is 0 (silently skipped).

### Tie-Breaking (D-03)
- **D-03:** When two instruments have identical total scores, break ties alphabetically by instrument id (stable, deterministic). This ensures `catalog.recommend("warm pad")` always returns the same result.

### Zero-Score Handling (D-04)
- **D-04:** If all instruments score 0 (no tokens match any affinity key), `catalog.recommend()` returns `None`. `list_descriptors()` still works normally. Tools should handle `None` return gracefully with a helpful message.

### recommend() Return Format (D-05)
- **D-05:** Returns a dict with these keys:
  ```python
  {
      "id": "wavetable",
      "name": "Wavetable",
      "score": 1.65,
      "browser_path": "Instruments/Wavetable",   # profile["browser"]["root"]
      "category_hint": "Pads",                    # best matching browser category
      "reasoning": "Best match for 'warm pad': Wavetable scores 1.65 — lush evolving pads with wavetable morphing"
  }
  ```
  Returns `None` if no profiles loaded or all scores are 0.

### Category Hint Derivation (D-06)
- **D-06:** Derive `category_hint` by finding the first role token in the query (e.g., "pad" from "warm pad") and looking it up in the winning instrument's `browser["categories"]` dict. If no role token maps to a category, use the first entry in `browser["categories"]`. If categories is empty, omit (empty string).

### Reasoning Format (D-07)
- **D-07:** One-line string: `f"Best match for '{original_descriptor}': {name} scores {score:.2f} — {top_strength}"` where `top_strength` is `profile["strengths"][0]`.

### Descriptor Vocabulary Source (D-08)
- **D-08:** `list_descriptors()` derives the vocabulary dynamically from the union of all registered profiles' affinity keys. Collects all keys from `descriptor_affinities["role"]` across all profiles (deduped, sorted) and all keys from `descriptor_affinities["character"]` (deduped, sorted). Returns `{"role": [...], "character": [...]}`. No separate taxonomy file -- vocabulary is always in sync with profiles.

### list_descriptors() Return Format (D-09)
- **D-09:** Returns `{"role": sorted_list, "character": sorted_list}` where each list contains all unique tag strings found across all 6 profiles for that axis.

### Module Location (D-10)
- **D-10:** `recommend()` and `list_descriptors()` added as new public functions to the existing `MCP_Server/sounds/catalog.py`. No new Python module. Both functions call `_ensure_initialized()` like existing functions.

### sounds.py Tool Module (D-11)
- **D-11:** Create `MCP_Server/tools/sounds.py` with `list_sound_descriptors` MCP tool. Phase 38 will add `get_sound_recommendation` and `get_instrument_profile` to this same file. Register `sounds` in `tools/__init__.py` in Phase 37 (alongside the existing imports).

### list_sound_descriptors Tool Behavior (D-12)
- **D-12:** `list_sound_descriptors` takes no parameters. Returns JSON of `catalog.list_descriptors()` result. Error handling follows the `format_error` pattern from genres.py. The docstring should explain the two axes (role and character) and give examples of each.

### SC4 Differentiation Gate (D-13)
- **D-13:** The plan must include a verification step that calls `catalog.recommend(tag)` for every tag returned by `catalog.list_descriptors()` and asserts that at least 4 different instruments appear as top-1 across all single-tag queries (proving meaningful differentiation across the 6 instruments). Any two tags producing identical top-1 is acceptable only if documented.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pattern References
- `MCP_Server/sounds/catalog.py` — Add recommend() and list_descriptors() here; follows existing _ensure_initialized pattern
- `MCP_Server/tools/genres.py` — MCP tool pattern: @mcp.tool(), json.dumps, format_error, Context param
- `MCP_Server/tools/__init__.py` — Add `sounds` to the import line here to register

### Existing Profile Data
- `MCP_Server/sounds/wavetable.py` — Affinity keys: role={pad, texture, lead, bass, keys}, character={evolving, warm, bright, dark, lush, aggressive}
- `MCP_Server/sounds/analog.py` — Affinity keys: role={bass, lead, keys, pad, texture}, character={warm, punchy, dark, bright, aggressive, evolving}
- `MCP_Server/sounds/operator.py` — Affinity keys: role={keys, bass, lead, pad, texture}, character={bright, punchy, aggressive, warm, dark, evolving}
- `MCP_Server/sounds/drift.py` — Affinity keys: role={bass, lead, keys, pad, texture}, character={warm, dark, evolving, punchy, bright, aggressive}
- `MCP_Server/sounds/simpler.py` — Affinity keys: role={keys, bass, lead, pad, texture}, character={organic, warm, bright, punchy, evolving, aggressive}
- `MCP_Server/sounds/drum_rack.py` — Affinity keys: role={kick, snare, hihat, percussion, pad, lead}, character={punchy, tight, aggressive, bright, warm, evolving}

### Requirements
- `.planning/REQUIREMENTS.md` — PKG-02 (scoring engine), SREC-02 (list_sound_descriptors tool)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `catalog._ensure_initialized()` — call this at the start of recommend() and list_descriptors()
- `catalog._registry` — dict of {id: profile_dict} after initialization
- `format_error` from `MCP_Server.connection` — error response helper used by all tools
- `json.dumps` return pattern — all MCP tools return JSON strings
- `tools/__init__.py` import line — one-liner; add `sounds` to the from . import list

### Established Patterns
- `@mcp.tool()` decorator from `MCP_Server.server import mcp`
- `from mcp.server.fastmcp import Context` for ctx parameter
- Try/except with `format_error` in every tool
- `from MCP_Server.sounds import recommend, list_descriptors` (or from catalog directly)

### Integration Points
- `MCP_Server/sounds/catalog.py` → add recommend() and list_descriptors() (no other file changes in sounds/)
- `MCP_Server/tools/sounds.py` → new file, list_sound_descriptors tool
- `MCP_Server/tools/__init__.py` → add `sounds` import

</code_context>

<specifics>
## Specific Ideas

- The scoring loop pseudocode:
  ```python
  def recommend(descriptor: str) -> Optional[dict]:
      _ensure_initialized()
      tokens = [t.strip(".,!?") for t in descriptor.lower().split()]
      tokens = [t for t in tokens if t]
      scores = {}
      for profile_id, profile in _registry.items():
          total = 0.0
          affinities = profile.get("descriptor_affinities", {})
          for token in tokens:
              total += affinities.get("role", {}).get(token, 0.0)
              total += affinities.get("character", {}).get(token, 0.0)
          scores[profile_id] = total
      if not scores or max(scores.values()) == 0.0:
          return None
      best_id = max(scores, key=lambda k: (scores[k], [-ord(c) for c in k]))  # desc score, then alpha
      # ... build return dict
  ```
  Actually tie-breaking: `max(scores, key=lambda k: (scores[k], k))` with reversed alpha needs careful handling. Simplest: sort items by (-score, id) and take first.

- list_sound_descriptors docstring should include: "Returns role tags (bass, lead, pad, kick, snare, hihat...) and character tags (warm, bright, dark, evolving, punchy...) derived from all instrument profiles."

</specifics>

<deferred>
## Deferred Ideas

- Multi-word phrase matching (e.g., treating "drum machine" as a phrase rather than ["drum", "machine"]) — Phase 37 uses token-level only
- Score normalization / TF-IDF weighting — plain sum is sufficient for v1.5
- Genre-aware recommendations (SREC-04) — post-v1.5
- Fuzzy matching / stemming for descriptor tokens — out of scope

</deferred>

---

*Phase: 37-descriptor-taxonomy-and-scoring-engine*
*Context gathered: 2026-03-31 (auto mode)*
