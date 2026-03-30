# Phase 29: Device Parameter Catalog and Role Taxonomy - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Date:** 2026-03-28
**Phase:** 29 — Device Parameter Catalog and Role Taxonomy

---

## Q1: Catalog Bootstrap Process

**Question:** How should the catalog be populated with live-verified parameter data?

**Options presented:**
- One-time script → static file *(Recommended)*
- Runtime query, lazily cached
- Runtime query, written to disk

**Selected:** One-time script → static file

---

## Q2: Catalog Storage Format

**Question:** Where does the catalog live in the codebase?

**Options presented:**
- Single catalog.py module *(Recommended)*
- One file per device
- JSON file in repo

**Selected:** Single catalog.py module — `MCP_Server/devices/catalog.py` with a `CATALOG` dict keyed by device class name

---

## Q3: MCP Tool Surface

**Question:** What MCP tools should be exposed for catalog and role access?

**Options presented:**
- Per-device + role tool *(Recommended)*
- Full catalog dump tool
- Three-tool surface

**Selected:** Per-device + role tool — `get_device_catalog(device_name)` + `get_role_taxonomy()`

---

## Q4: Unit Conversion Representation

**Question:** How should normalized-to-natural-unit conversion formulas be stored in the catalog?

**Options presented:**
- Structured dict *(Recommended)*
- Human-readable string only
- No formulas in catalog

**Selected:** Structured dict — `{"type": "log", "natural_min": 20, "natural_max": 22050, "unit": "Hz"}`

---

## Q5: Role Taxonomy Richness

**Question:** How rich should the role taxonomy entries be?

**Options presented:**
- Bare list *(Recommended)*
- Role + gain targets
- Role + description + devices

**Selected:** Bare list — `["kick", "bass", "lead", "pad", "chords", "vocal", "atmospheric", "return", "master"]`

---

*All 5 areas: user accepted recommended defaults throughout.*
