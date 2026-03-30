# Phase 31: Apply Recipe and Batch Parameter Tools - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.

**Session:** 2026-03-28
**Facilitator:** Claude (gsd:discuss-phase)

---

## Atomicity Strategy

**Q: How should apply_mix_recipe handle the load-then-set sequence?**
Options: New RS command: apply_recipe / MCP-side orchestration / Hybrid: new batch-set RS command
**Selected:** New RS command: apply_recipe
*Single RS handler does load + block until device appears + set all params in one trip. All atomicity logic in RS Python.*

**Q: How should the RS handler resolve device class names to browser paths?**
Options: Hardcoded paths in RS handler / MCP passes path in command / RS queries browser at apply time
**Selected:** Hardcoded paths in RS handler
*Dict in RS handler maps catalog class names to known browser paths. Reliable for 12 built-in devices.*

**Q: Where should natural-unit → normalized conversion happen?**
Options: MCP side before sending / RS side using catalog data
**Selected:** MCP side before sending
*MCP reads recipe + catalog, converts all values to normalized floats, sends converted payload to RS. RS handler receives only normalized values.*

---

## Device Conflict Handling

**Q: When apply_mix_recipe runs on a track that already has devices, what should happen?**
Options: Update params in place / Clear and reload everything / Fail if conflict detected
**Selected:** Update params in place
*Find existing device by class_name, update its params. Only load missing devices. Preserves user work outside recipe scope.*

**Q: How should RS handler identify 'this device is an EQ Eight'?**
Options: Match by class name / Match by device name string
**Selected:** Match by class name
*`device.class_name == 'Eq8'` (or Compressor2, etc.) — same keys as CATALOG. First match wins on duplicates.*

---

## Master Bus Recipe Scope

**Q: How should Phase 31 handle apply_master_recipe?**
Options: Author full master recipes in Phase 31 / Apply Phase 30 minimal recipes / Defer apply_master_recipe to Phase 34
**Selected:** Author full master recipes in Phase 31
*Phase 31 adds GlueCompressor + MultibandDynamics + Limiter recipes for 4 core genres. Phase 34 extends to 8 more genres.*

---

## Sidechain Routing (SIDE-01)

**Q: How should sidechain source setting by track name work architecturally?**
Options: New RS command: set_sidechain_source / MCP resolves name, RS gets index
**Selected:** New RS command: set_sidechain_source
*RS handler receives source_track_name, resolves name → index using Live.Song.tracks at apply time.*

**Q: What should happen when the source track name isn't found?**
Options: Return error, abort apply / Apply recipe without sidechain
**Selected:** Return error, abort apply
*Fail with clear error message naming the unresolved track. No partial state. User fixes track name and retries.*
