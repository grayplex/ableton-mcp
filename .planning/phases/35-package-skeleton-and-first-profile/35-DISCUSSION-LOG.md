# Phase 35: Package Skeleton and First Profile - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-03-31
**Phase:** 35-package-skeleton-and-first-profile
**Areas discussed:** Profile data shape, Browser path format, Alias & lookup behavior

---

## Profile Data Shape

### Descriptor Affinities Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Two-axis dict | Separate 'role' and 'character' sub-dicts with 0.0-1.0 weights | ✓ |
| Flat dict | Single level with all tags mixed | |
| Three-axis dict | Add a third axis beyond role/character | |

**User's choice:** Two-axis dict (Recommended)
**Notes:** Matches ROADMAP wording and keeps scoring clean for Phase 37.

### Schema Version

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal constant only | Just export a PROFILE dict, no schema version | ✓ |
| Include schema version | Add 'schema_version' field to PROFILE dict | |

**User's choice:** Minimal constant only (Recommended)
**Notes:** Add validation in Phase 36 if needed, same way genres/schema.py was added later.

### Strengths/Weaknesses Format

| Option | Description | Selected |
|--------|-------------|----------|
| Short phrase list | List of 3-5 short phrases | ✓ |
| Sentence descriptions | Full sentences | |
| You decide | Claude picks the format | |

**User's choice:** Short phrase list (Recommended)
**Notes:** Compact, easy for scoring engine to use.

### Sonic Character Format

| Option | Description | Selected |
|--------|-------------|----------|
| Single string | One concise paragraph describing sonic identity | ✓ |
| Structured sub-fields | Broken into summary/texture/sweet_spot fields | |

**User's choice:** Single string (Recommended)
**Notes:** Mirrors how genre blueprints describe things.

---

## Browser Path Format

### Path Storage Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Root + categories dict | Separate root path and categories dict mapping roles to sub-paths | ✓ |
| Flat path list | List of full paths | |
| Root path only | Just the instrument root | |

**User's choice:** Root + categories dict (Recommended)
**Notes:** Root validates loadability; categories guide browsing.

### Validation Failure Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Log warning, keep path | Profile loads normally but logs a warning | ✓ |
| Fail hard | Raise an error if path doesn't validate | |
| You decide | Claude picks the behavior | |

**User's choice:** Log warning, keep path (Recommended)
**Notes:** Validation is a development-time check, not a runtime gate. Profiles work offline too.

### Validation Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Root only | Only validate instrument root path against live Ableton | ✓ |
| Validate all paths | Validate root AND each category path | |

**User's choice:** Root only (Recommended)
**Notes:** Category sub-paths vary by Live edition and installed packs.

---

## Alias & Lookup Behavior

### Abbreviation Support

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, define in profile | Each profile includes an 'aliases' list | ✓ |
| No abbreviations | Only full name and normalization | |
| You decide | Claude picks aliases per instrument | |

**User's choice:** Yes, define in profile (Recommended)
**Notes:** Natural for Claude to use short names. Matches genre blueprint aliases pattern.

### Unknown Instrument Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Return None | Return None for unknown names | ✓ |
| Raise KeyError | Raise an exception | |
| Return error dict | Return {"error": "..."} dict | |

**User's choice:** Return None (Recommended)
**Notes:** Matches how mixing/catalog returns None for unknown genres.

### Display Name Acceptance

| Option | Description | Selected |
|--------|-------------|----------|
| Accept both | Normalize input with lowercase + underscore replacement | ✓ |
| Module ID only | Require exact module ID | |

**User's choice:** Accept both (Recommended)
**Notes:** Same normalization as genres/mixing catalogs. Zero friction for callers.

---

## Claude's Discretion

No areas deferred to Claude's discretion in this phase.

## Deferred Ideas

None -- discussion stayed within phase scope.
