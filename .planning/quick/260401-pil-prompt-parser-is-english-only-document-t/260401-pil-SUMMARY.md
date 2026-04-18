---
phase: quick
plan: 260401-pil
subsystem: prompt-parser
tags: [documentation, lexicon, english-only]
dependency_graph:
  requires: []
  provides: [english-only-documentation]
  affects: [MCP_Server/prompt/lexicon.py, MCP_Server/refinement/lexicon.py, MCP_Server/prompt/parser.py]
tech_stack:
  added: []
  patterns: []
key_files:
  modified:
    - MCP_Server/prompt/lexicon.py
    - MCP_Server/refinement/lexicon.py
    - MCP_Server/prompt/parser.py
decisions:
  - Documented English-only limitation as docstring additions only, no functional changes
metrics:
  duration: ~2m
  completed: "2026-04-01"
---

# Quick Task 260401-pil: Document English-Only Limitation in Prompt Parser

Docstring-only changes documenting that both lexicons and the parser are English-only, with non-English tokens falling through to raw_descriptors.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Document English-only limitation in lexicons and parser | 22f0d9c | MCP_Server/prompt/lexicon.py, MCP_Server/refinement/lexicon.py, MCP_Server/prompt/parser.py |

## Changes Made

### MCP_Server/prompt/lexicon.py
- Added "Language: English-only" paragraph to module docstring explaining that all lookup tables contain English terms exclusively and non-English tokens fall through to raw_descriptors.

### MCP_Server/refinement/lexicon.py
- Added "Language: English-only" note to module docstring explaining that all adjective keys are English.

### MCP_Server/prompt/parser.py
- Added note to `classify_prompt` function docstring explaining that non-English tokens (length > 2) are collected in raw_descriptors so downstream consumers can surface them.

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- All three files import without error
- "English-only" appears in both lexicon module docstrings
- "raw_descriptors" fallback documented in parser classify_prompt docstring
- All 32 existing tests pass

## Known Stubs

None.

## Self-Check: PASSED
