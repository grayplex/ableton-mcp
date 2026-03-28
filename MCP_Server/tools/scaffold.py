"""Scaffold tools: write production plans into Ableton Arrangement view.

Pure helper functions (_deduplicate_roles, _bar_to_beat) are used by the
scaffold_arrangement MCP tool to convert plan data into Ableton commands.
"""


def _deduplicate_roles(sections: list[dict]) -> list[str]:
    """Flatten section roles into unique track names with dedup suffixes.

    Each unique role gets one track. If a role appears in multiple sections,
    additional occurrences get numbered suffixes: "lead", "lead 2", "lead 3".

    Track names are ordered by first appearance across sections.

    Args:
        sections: List of section dicts, each with a "roles" list.

    Returns:
        List of deduplicated track name strings.
    """
    role_counts: dict[str, int] = {}
    for section in sections:
        section_seen: set[str] = set()
        for role in section.get("roles", []):
            if role not in section_seen:
                section_seen.add(role)
                role_counts[role] = role_counts.get(role, 0) + 1

    # Build output: for each role, emit base name + numbered variants
    # Preserve first-seen order from sections
    seen_roles: list[str] = []
    for section in sections:
        for role in section.get("roles", []):
            if role not in seen_roles:
                seen_roles.append(role)

    result: list[str] = []
    for role in seen_roles:
        count = role_counts.get(role, 0)
        if count <= 0:
            continue
        result.append(role)
        for i in range(2, count + 1):
            result.append(f"{role} {i}")

    return result


def _bar_to_beat(bar_start: int, beats_per_bar: float) -> float:
    """Convert a 1-based bar number to a 0-based beat position.

    Args:
        bar_start: 1-based bar number (bar 1 = beat 0).
        beats_per_bar: Number of beats per bar, derived from time signature
                       as numerator * (4 / denominator).

    Returns:
        Beat position as float.
    """
    return (bar_start - 1) * beats_per_bar
