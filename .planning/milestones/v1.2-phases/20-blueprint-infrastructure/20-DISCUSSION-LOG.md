# Phase 20: Blueprint Infrastructure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 20-blueprint-infrastructure
**Areas discussed:** Blueprint data format, Genre module organization, Schema enforcement, Blueprint content depth

---

## Blueprint Data Format

| Option | Description | Selected |
|--------|-------------|----------|
| Python dicts in .py files | Matches existing codebase pattern. Catalog imports directly. Type checking works. | ✓ |
| JSON files | Separate data from code. Easy to read/edit. New pattern for the project. | |
| YAML files | Most readable for dense content. New dependency. New pattern. | |

**User's choice:** Python dicts in .py files — user initially considered JSON for editing but chose Python for consistency with existing codebase patterns.

| Option | Description | Selected |
|--------|-------------|----------|
| Pure data only | Each genre file exports one dict. No functions. Declarative data, logic in catalog/schema. | ✓ |
| Data + helpers | Genre files can include helper functions. More flexible but blurs data/logic boundary. | |

**User's choice:** Pure data only
**Notes:** None

---

## Genre Module Organization

| Option | Description | Selected |
|--------|-------------|----------|
| MCP_Server/genres/ | New top-level package alongside theory/. Clean separation. | ✓ |
| MCP_Server/theory/genres/ | Nested under theory. Groups all music intelligence together. | |

**User's choice:** MCP_Server/genres/

| Option | Description | Selected |
|--------|-------------|----------|
| One file per genre | house.py, techno.py, etc. Easy to find and edit. 12 files total. | ✓ |
| Grouped by tier | p0_genres.py, p1_genres.py, p2_genres.py. Fewer files. | |
| Single genres.py | All genres in one file. Simple but large. | |

**User's choice:** One file per genre

| Option | Description | Selected |
|--------|-------------|----------|
| Same file as parent | house.py exports base + subgenres dict. Keeps related data together. | ✓ |
| Separate subgenre files | house_deep.py, house_tech.py, etc. More granular but 40+ files. | |

**User's choice:** Same file as parent
**Notes:** None

---

## Schema Enforcement

| Option | Description | Selected |
|--------|-------------|----------|
| TypedDict + manual validation | IDE support + validate_blueprint() at import time. No new deps. | ✓ |
| Pydantic models | Strongest validation. New dependency and pattern. | |
| Plain dict validation | No TypedDict. Simplest but no IDE autocompletion. | |

**User's choice:** TypedDict + manual validation

| Option | Description | Selected |
|--------|-------------|----------|
| Raise exception (fail-fast) | ValueError stops server from starting with bad data. | |
| Log warning + skip genre | Bad genre excluded but server still starts. | |
| Raise per-genre, catch at catalog | ValueError per genre, catalog catches/logs/excludes, server starts with valid genres. | ✓ |

**User's choice:** Custom — raise exception per genre but don't stop server. Catalog catches ValueError, logs error, excludes malformed genre, server starts with remaining valid genres.
**Notes:** User wanted a middle ground: make errors visible (exceptions) but don't prevent the server from starting.

---

## Blueprint Content Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Structured data | Typed fields per dimension. Enables palette bridge. | ✓ |
| Prose text | String descriptions per dimension. Claude reads as context. | |
| Structured + prose notes | Typed fields + notes string per dimension for nuance. | |

**User's choice:** Structured data

| Option | Description | Selected |
|--------|-------------|----------|
| Scales + chord types + progressions | Full harmony data. All names match theory engine types. | ✓ |
| Scales + chord types only | Skip progressions to avoid duplication with progression engine. | |

**User's choice:** Scales + chord types + progressions

| Option | Description | Selected |
|--------|-------------|----------|
| Generic roles | "kick", "bass", "pad" — Claude maps to Ableton devices contextually. | ✓ |
| Ableton-specific suggestions | "Operator (FM bass)" — specific device suggestions. | |
| Both: role + suggestion | Role with optional Ableton suggestion. | |

**User's choice:** Generic roles

| Option | Description | Selected |
|--------|-------------|----------|
| Section sequence + bar counts | Concrete arrangement templates with bar lengths. | ✓ |
| Section names only | Just names/order, Claude decides lengths. | |

**User's choice:** Section sequence + bar counts
**Notes:** Remaining dimensions (rhythm, mixing, production tips) left to Claude's discretion, following the structured data pattern.

---

## Claude's Discretion

- Rhythm, mixing, and production tips dimension internal structure
- Catalog auto-discovery mechanism
- Alias resolution implementation
- Subgenre merge strategy details
- Internal naming conventions for exported dicts

## Deferred Ideas

None — discussion stayed within phase scope
