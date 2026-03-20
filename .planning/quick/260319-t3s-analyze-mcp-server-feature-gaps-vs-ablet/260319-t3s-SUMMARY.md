---
phase: quick
plan: 260319-t3s
subsystem: analysis
tags: [gap-analysis, lom, documentation]
dependency_graph:
  requires: [phase-11-gap-report]
  provides: [lom-gap-analysis, future-priority-list]
  affects: [future-development-phases]
tech_stack:
  added: []
  patterns: [pdf-extraction, source-code-analysis]
key_files:
  created:
    - .planning/quick/260319-t3s-analyze-mcp-server-feature-gaps-vs-ablet/LOM-GAP-ANALYSIS.md
  modified: []
decisions:
  - Wavetable sound design identified as highest-priority remaining gap
  - Compressor sidechain routing second priority (mixing essential)
  - View classes (8 total) classified as low AI value / out of scope
  - Device-specific classes with only generic-parameter features classified as low priority
metrics:
  duration: 8min
  completed: "2026-03-19"
---

# Quick Task 260319-t3s: LOM Gap Analysis Summary

Comprehensive gap analysis comparing 144 Remote Script commands and 141 MCP tools against all 43 LOM classes from the 171-page Max9-LOM-en.pdf reference.

## Tasks Completed

| Task | Name | Commit | Key Output |
|------|------|--------|------------|
| 1 | Extract implementation inventory | bf61c2b | Section 1: 144 commands + 141 tools organized by 15 domains |
| 2 | LOM PDF analysis and gap prioritization | bf61c2b | Sections 2-6: 43 classes cataloged, gaps identified and ranked |

## Key Findings

### Coverage Status
- **9 classes fully covered:** Song, Track, Clip, ClipSlot, Scene, MixerDevice, GroovePool, Groove, CuePoint
- **6 classes substantially covered:** Device, PluginDevice, SimplerDevice, DrumPad, RackDevice, Sample
- **4 classes partially covered:** DeviceParameter, Chain, ChainMixerDevice, DeviceIO
- **24 classes not covered** (8 View classes, 3 App/Control, 13 device-specific)

### High-Value Gaps (11 features)
1. WavetableDevice -- wavetable selection and modulation matrix
2. CompressorDevice -- sidechain routing
3. RackDevice -- macro variations, chain management, macro add/remove
4. DrumChain -- in_note assignment and choke groups
5. DeviceParameter -- automation_state and re_enable_automation

### Medium-Value Gaps (16 features)
DriftDevice mod matrix, LooperDevice controls, HybridReverbDevice IR selection, SpectralResonatorDevice modes, Eq8Device processing modes, TakeLane support, TuningSystem, and others.

### Out of Scope (confirmed low value)
All 8 View classes, ControlSurface (hardware), this_device (M4L), Application (monitoring/UI), DrumCellDevice and ShifterDevice (no unique members beyond DeviceParameter).

## Deviations from Plan

None -- plan executed exactly as written. Both tasks combined into a single document write since the implementation inventory and PDF analysis were interleaved for efficiency.

## Decisions Made

1. **WavetableDevice is the top priority** -- Ableton's flagship synth has wavetable browsing and modulation matrix features that are completely inaccessible through generic DeviceParameter access.
2. **Compressor sidechain routing is #2** -- The most common mixing technique (sidechain compression) requires CompressorDevice-specific routing that generic params cannot provide.
3. **View classes are out of scope** -- All 8 View classes (Application.View, Clip.View, Device.View, Eq8Device.View, RackDevice.View, SimplerDevice.View, Song.View, Track.View) serve UI management purposes not useful for AI music production.
4. **Many device-specific classes are low priority** -- DrumCellDevice, ShifterDevice, MeldDevice, RoarDevice expose only parameters already accessible through the generic DeviceParameter interface.
