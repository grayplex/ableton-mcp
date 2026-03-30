# Phase 32: Device State Reader and Gain Staging - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 32-device-state-reader-and-gain-staging
**Areas discussed:** get_mix_state scope, Gain staging meter source, Role resolution

---

## get_mix_state Scope

| Option | Description | Selected |
|--------|-------------|----------|
| All tracks + returns + master | Full session snapshot — every track type included | ✓ |
| Regular tracks only | Simpler output but loses return and master bus state | |

**User's choice:** All tracks + returns + master
**Notes:** Matches "every track" language in STATE-01; Phase 33 needs master chain state.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Device params only | Per-device parameter snapshots only | ✓ |
| Device params + mixer state | Also include volume_db, pan, sends per track | |

**User's choice:** Device params only
**Notes:** Volume/pan readable via existing tools; keeps output focused on what Phase 33 needs.

---

## Gain Staging Meter Source

| Option | Description | Selected |
|--------|-------------|----------|
| output_meter_level | Real-time signal level, warn when 0 (not playing) | ✓ |
| Fader position via _to_db() | Always readable but measures setting not signal | |
| Report both | Return both fader_db and meter_db | |

**User's choice:** output_meter_level
**Notes:** Warn with "all meters are 0 — play the session first" when all read 0.

---

## Role Resolution

| Option | Description | Selected |
|--------|-------------|----------|
| Infer from track name | Case-insensitive substring match against ROLES list | ✓ |
| User-provided role_map param | Explicit {track_index: role} mapping | |
| Hybrid: infer + optional override | Name inference with optional role_map correction | |

**User's choice:** Infer from track name
**Notes:** Tracks with no role match are still reported with level but marked role: null. MIDI tracks with no devices excluded per GAIN-02.

---

## Claude's Discretion

- Exact dBFS target ranges per role
- Where gain targets live (gain_targets.py or inline)
- output_meter_level → dBFS conversion formula
- Whether get_mix_state includes tracks with zero devices or skips them
- New RS command name(s) for session-wide device state read

## Deferred Ideas

None.
