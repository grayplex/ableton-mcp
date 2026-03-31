# Stack Research

**Domain:** Sound selection intelligence for Ableton MCP (v1.5)
**Researched:** 2026-03-30
**Confidence:** HIGH

## Core Finding: No New Dependencies Required

The v1.5 sound selection intelligence feature is **pure authored data + Python stdlib logic**. No new libraries are needed. This is the correct approach because:

1. The descriptor-to-instrument mapping is **curated knowledge**, not ML/NLP inference
2. The matching is against a **finite, authored tag set** (not free-text search)
3. The project already has a proven pattern for this exact kind of data (genres, mix recipes, device catalog)
4. Claude picks descriptors from `list_sound_descriptors` output -- there is no free-text fuzzy matching scenario

## Recommended Stack

### Core Technologies (Already In Place -- No Changes)

| Technology | Version | Purpose | v1.5 Role |
|------------|---------|---------|-----------|
| Python | 3.11 | Runtime (Ableton embedded + MCP server) | All v1.5 code is server-side only |
| FastMCP (mcp[cli]) | >=1.3.0 | MCP tool registration via `@mcp.tool()` | 3 new tools: `get_sound_recommendation`, `list_sound_descriptors`, `get_instrument_profile` |
| pkgutil + importlib | stdlib | Auto-discovery of data modules | Discovers instrument profile modules, same as genres/mixing catalogs |

### Supporting Libraries (None New)

| Library | Version | Role in v1.5 | Notes |
|---------|---------|--------------|-------|
| `mcp[cli]` | >=1.3.0 | Register 3 new tools | No changes needed to dependency |
| `music21` | >=9.0 | **Not used by v1.5** | Sound selection is instrument/timbre domain, not theory |
| `json` | stdlib | Serialize tool responses | Already used by all tool modules |
| `copy` | stdlib | Deep-copy instrument profiles for safe return | Same pattern as `genres/catalog.py` line 167 |
| `logging` | stdlib | Log discovery errors/warnings | Same pattern as existing catalogs |

### Development Tools (Already In Place)

| Tool | Role in v1.5 | Notes |
|------|--------------|-------|
| pytest / pytest-asyncio | Unit tests for catalog, descriptor matching, edge cases | Same test patterns as v1.2-v1.4 |
| ruff | Lint new `instruments/` package | Already configured in pyproject.toml |
| tiktoken | Measure tool output token budget if needed | Dev-only, already in dev deps |

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------------|
| `thefuzz` / `fuzzywuzzy` | Overkill for matching against a finite authored tag set; adds C dependency (python-Levenshtein) for performance; descriptor tags are exact-match after normalization | Normalize input (lowercase, strip, underscore) + alias dict -- same as `mixing/catalog.py` `_normalize()` |
| `rapidfuzz` | Same rationale as thefuzz; faster C implementation but still unnecessary for ~50-100 tags | Alias normalization covers all realistic inputs |
| `sentence-transformers` / any ML embedding | Massive dependency tree (torch, transformers, ~2GB); latency per call; the tag set is small enough for explicit mapping; completely disproportionate to the problem | Authored descriptor-to-instrument mappings |
| `scikit-learn` | TF-IDF or cosine similarity for descriptor matching is over-engineering a 50-tag lookup | Alias dict + normalize |
| `spacy` / `nltk` | NLP tokenization/lemmatization unnecessary when tags are authored and Claude picks from a known list | Direct string matching after normalization |
| `difflib.SequenceMatcher` | stdlib but still unnecessary; tempting "just in case" addition that complicates matching semantics and makes behavior less predictable | Clean alias dict with explicit mappings |
| `pydantic` | Data validation library; the project uses plain dicts validated by custom schema functions (see `genres/schema.py`) | Keep existing validation pattern for consistency |
| `PyYAML` / `toml` | External data format loaders; the project convention is Python dicts in .py files | Python modules with dict constants |

**Why "no fuzzy matching" is correct:** The `list_sound_descriptors` tool gives Claude the exact valid tags. Claude does not need to guess or approximate -- it calls `list_sound_descriptors`, picks a tag, passes it to `get_sound_recommendation`. This is identical to how `list_recipes()` works for mix recipes. Fuzzy matching solves a problem that does not exist in this architecture.

## What DOES Need Changing

### 1. pyproject.toml `[tool.setuptools]` packages list

Current:
```toml
packages = ["MCP_Server", "MCP_Server.tools", "MCP_Server.theory"]
```

Must add the new `instruments` package:
```toml
packages = [
    "MCP_Server",
    "MCP_Server.tools",
    "MCP_Server.theory",
    "MCP_Server.genres",
    "MCP_Server.devices",
    "MCP_Server.mixing",
    "MCP_Server.instruments",
]
```

Note: `genres`, `devices`, and `mixing` are likely already importable via editable install but should be explicitly listed for correctness. Adding them is a housekeeping fix, not a v1.5 requirement per se.

### 2. tools/__init__.py import line

Add the new tool module to the single-line import that triggers `@mcp.tool()` registration:
```python
from . import ..., sounds  # noqa: F401
```

(Module name `sounds` for the tool file; the data package is `instruments`.)

### 3. New package: `MCP_Server/instruments/`

Following the exact pattern of `MCP_Server/genres/` and `MCP_Server/mixing/`:

```
MCP_Server/instruments/
    __init__.py          # Public API: get_instrument_profile, get_recommendation, list_descriptors
    catalog.py           # Auto-discovery via pkgutil, descriptor reverse index, matching logic
    wavetable.py         # INSTRUMENT dict constant
    analog.py            # INSTRUMENT dict constant
    operator.py          # INSTRUMENT dict constant
    drift.py             # INSTRUMENT dict constant
    simpler.py           # INSTRUMENT dict constant
    drum_rack.py         # INSTRUMENT dict constant
```

### 4. New tool file: `MCP_Server/tools/sounds.py`

Three `@mcp.tool()` functions wrapping the `instruments` package public API. Follows the same pattern as `tools/mixing.py` wrapping `mixing/catalog.py`.

## Descriptor Matching Strategy

The matching approach uses **exact match after normalization**, with an alias layer:

```python
def _normalize(descriptor: str) -> str:
    """Lowercase, collapse whitespace, underscores for spaces/hyphens."""
    return descriptor.strip().lower().replace(" ", "_").replace("-", "_")
```

The catalog builds two indexes at discovery time:

1. **descriptor_tag -> list of (instrument_id, category_path, reasoning)** -- the core recommendation index
2. **instrument_id -> full profile dict** -- for `get_instrument_profile`

When `get_sound_recommendation("warm pad")` is called:
1. Normalize: `"warm_pad"`
2. Look up in descriptor index
3. Return matching instrument(s) with category path and reasoning

For descriptors with multiple matching instruments, the catalog returns **all matches ranked by authored priority** (first instrument in the list is the strongest match). This lets Claude make a contextual choice or present options.

## Integration Points

| Integration | How | Risk |
|-------------|-----|------|
| MCP tool registration | `@mcp.tool()` in `tools/sounds.py`, imported in `tools/__init__.py` | None -- proven pattern |
| Browser navigation | Tool returns `category_path` (e.g., "Wavetable/Pads/Warm"); Claude uses existing `navigate_browser` + `load_browser_item` tools | None -- decoupled; sound recommendation outputs a path, browser tools consume it |
| No Remote Script changes | All logic is MCP server-side; no socket commands needed | None -- server-only feature |
| No genre dependency | Descriptors are instrument-intrinsic, not genre-scoped | Intentional -- keeps v1.5 orthogonal to v1.2 genres |

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Alias normalization + dict | `thefuzz` fuzzy matching | Only if descriptors were user-typed free text (they are not -- Claude picks from a list) |
| Python dicts for profiles | YAML/JSON data files | Only if non-Python tools needed to read profiles; Python dicts are the established project convention |
| pkgutil auto-discovery | Manual registration dict | Never -- auto-discovery is proven in genres and mixing; avoids registration bugs when adding instruments |
| One file per instrument | Single large file | Never for 6 instruments -- one-file-per-entity is the project convention and aids maintainability |
| Reverse index at import time | On-demand linear scan | Reverse index is O(1) lookup vs O(n*m) scan; built once at import time; negligible startup cost for 6 instruments |

## Version Compatibility

No new packages means no new compatibility concerns. Existing constraints unchanged:

| Constraint | Value | Impact on v1.5 |
|------------|-------|-----------------|
| Python >= 3.10 (MCP server) | pyproject.toml | All stdlib features used are available in 3.10+ |
| Python 3.11 (Ableton) | Ableton Live 12 | v1.5 is 100% server-side; no Remote Script changes |
| mcp[cli] >= 1.3.0 | pyproject.toml | 3 new tools, same `@mcp.tool()` registration pattern |

## Installation

No changes to installation. The existing install command covers everything:

```bash
# Existing install (unchanged)
pip install -e ".[dev]"
```

No new entries in `dependencies` or `[dependency-groups] dev`.

## Sources

- Codebase analysis: `MCP_Server/genres/catalog.py` -- pkgutil auto-discovery + alias normalization pattern (HIGH confidence)
- Codebase analysis: `MCP_Server/mixing/catalog.py` -- `_normalize()` + alias dict pattern (HIGH confidence)
- Codebase analysis: `MCP_Server/devices/__init__.py` -- dict-based lookup pattern (HIGH confidence)
- Codebase analysis: `MCP_Server/tools/__init__.py` -- tool registration via single import line (HIGH confidence)
- Codebase analysis: `pyproject.toml` -- current dependency list and setuptools packages (HIGH confidence)
- Domain knowledge: thefuzz/rapidfuzz/sentence-transformers are overkill for finite tag matching (HIGH confidence -- well-understood engineering tradeoff)

---
*Stack research for: v1.5 Sound Selection Intelligence*
*Researched: 2026-03-30*
