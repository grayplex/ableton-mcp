# Technology Stack: v1.2 Genre/Style Blueprints

**Project:** Ableton MCP v1.2
**Researched:** 2026-03-25

## Recommended Stack

### No New Dependencies

v1.2 requires **zero new packages**. Blueprints are static Python dicts served through existing FastMCP tools. The palette bridge calls existing theory engine functions (music21-backed).

### Existing Stack (unchanged)

| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| Python | 3.10+ (host), 3.11 (Ableton) | Runtime | Unchanged |
| mcp[cli] | >=1.3.0 | MCP server framework (FastMCP) | Unchanged |
| music21 | >=9.0 | Theory engine backend | Unchanged (used by palette bridge) |
| pytest | >=8.3 | Testing | Unchanged |
| ruff | >=0.15.6 | Linting | Unchanged |

### New Internal Modules (no external deps)

| Module | Purpose | Dependencies |
|--------|---------|--------------|
| `MCP_Server/blueprints/` | Blueprint library package | Python stdlib only |
| `MCP_Server/blueprints/catalog.py` | Registry + lookup | Genre modules |
| `MCP_Server/blueprints/schema.py` | Validation | Python stdlib (`typing`) |
| `MCP_Server/blueprints/genres/*.py` | Genre data | None |
| `MCP_Server/tools/blueprints.py` | MCP tool wrappers | `blueprints/`, `theory/`, `mcp` |

## Alternatives Considered

| Decision | Chosen | Alternative | Why Not |
|----------|--------|-------------|---------|
| Data format | Python dicts | JSON files | No runtime file I/O; matches PROGRESSION_CATALOG pattern |
| Data format | Python dicts | YAML files | Adds PyYAML dependency; no benefit over Python dicts |
| Data format | Python dicts | Markdown files | Unstructured; cannot filter by section; harder to parse |
| Delivery | MCP tools | MCP resources | Resources are app-controlled, not model-controlled; breaks autonomous genre detection |
| Delivery | MCP tools | MCP prompts | Prompts are user-triggered (slash commands); genre context should be automatic |
| Validation | Runtime dict checks | Pydantic models | Adds dependency; overkill for read-only reference data |
| Validation | Runtime dict checks | TypedDict | Could work but blueprints are too deeply nested for clean TypedDict usage |

## Package Configuration Changes

```toml
# pyproject.toml — add to existing [tool.setuptools] packages list
packages = [
    "MCP_Server",
    "MCP_Server.tools",
    "MCP_Server.theory",
    "MCP_Server.blueprints",        # NEW
    "MCP_Server.blueprints.genres",  # NEW
]
```

## Sources

- Existing `pyproject.toml` (dependency list, package configuration)
- Existing codebase patterns (Python catalogs in theory engine)

---
*Stack research for: v1.2 Genre/Style Blueprints*
*Researched: 2026-03-25*
