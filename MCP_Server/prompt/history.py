"""Session-scoped production brief history log.

Stores interpreted ProductionBrief results in-memory for the current
server session. Allows users to recall all prompts that have been
interpreted during a session, useful after context resets.

History is stored as a module-level list and resets when the server
process restarts (session-scoped, not persistent).
"""

import time

# ---------------------------------------------------------------------------
# In-memory log: list of brief entries, ordered chronologically.
# Each entry: {raw_prompt, brief, source, timestamp}
# ---------------------------------------------------------------------------

_BRIEF_LOG: list = []
_SESSION_START: float = time.time()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def record_brief(raw_prompt: str, brief: dict, source: str) -> None:
    """Append an interpreted brief to the session log.

    Args:
        raw_prompt: The original user prompt text.
        brief: The ProductionBrief dict returned by derive().
        source: Which tool recorded this ("interpret_prompt" or
                "interpret_prompt_to_plan").
    """
    _BRIEF_LOG.append({
        "raw_prompt": raw_prompt,
        "brief": brief,
        "source": source,
        "timestamp": time.time(),
    })


def get_briefs() -> list:
    """Return all brief entries (newest last).

    Returns a shallow copy so callers cannot mutate internal state.
    """
    return list(_BRIEF_LOG)


def clear_briefs() -> None:
    """Clear all brief history."""
    _BRIEF_LOG.clear()
