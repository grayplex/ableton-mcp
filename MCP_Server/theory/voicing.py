"""Voice leading library: smooth chord connections with parallel motion avoidance."""

from itertools import permutations

from MCP_Server.theory.chords import _make_note_obj, _midi_to_pitch
from MCP_Server.theory.progressions import _resolve_numeral_to_chord


def _has_parallel_motion(prev_midis, next_midis):
    """Check for parallel perfect 5ths or octaves between voice pairs.

    For each pair of voices (i, j), compute the interval (mod 12) in both
    the previous and next chord. If both are 7 (P5) or 0 (P8/unison),
    AND the voices moved in the same direction (not contrary/oblique),
    that's a parallel motion violation.

    Operates on the minimum length of the two arrays when sizes differ.

    Args:
        prev_midis: Sorted MIDI pitches of previous chord.
        next_midis: Sorted MIDI pitches of next chord.

    Returns:
        bool: True if parallel 5ths or octaves detected.
    """
    n = min(len(prev_midis), len(next_midis))
    for i in range(n):
        for j in range(i + 1, n):
            prev_interval = (prev_midis[j] - prev_midis[i]) % 12
            next_interval = (next_midis[j] - next_midis[i]) % 12

            # Both intervals are perfect 5ths or both are unisons/octaves
            if prev_interval == next_interval and prev_interval in (0, 7):
                # Check that both voices actually moved (not oblique motion)
                motion_i = next_midis[i] - prev_midis[i]
                motion_j = next_midis[j] - prev_midis[j]
                # Parallel = same direction, both moved
                if motion_i != 0 and motion_j != 0 and (motion_i > 0) == (motion_j > 0):
                    return True
    return False


def voice_lead_chords(source_midis, target_midis):
    """Voice-lead target chord to minimize movement from source, avoiding parallel 5ths/octaves.

    Algorithm:
        1. Generate candidate placements for each target pitch class near source center.
        2. Try all permutations (chords <= 5 notes).
        3. Filter out permutations that create parallel 5ths/octaves with source.
        4. Pick the permutation with minimum total movement.
        5. If ALL permutations have parallels, fall back to minimum movement (best effort).

    Args:
        source_midis: List of MIDI pitches for the source/previous chord.
        target_midis: List of MIDI pitches for the target/next chord.

    Returns:
        list[dict]: Re-voiced target chord as rich note objects
                    [{"midi": int, "name": str}, ...].
    """
    source_sorted = sorted(source_midis)
    center = sum(source_sorted) / len(source_sorted)

    # Generate candidates: place each target pitch class near source center
    target_pcs = [m % 12 for m in target_midis]
    candidates = []
    for pc in target_pcs:
        base = int(center) - (int(center) % 12) + pc
        options = [base - 12, base, base + 12]
        best = min(options, key=lambda x: abs(x - center))
        candidates.append(best)

    n_source = len(source_sorted)
    n_target = len(candidates)

    if n_target <= 5:
        best_perm = None
        best_cost = float("inf")
        # Also track the overall best (ignoring parallel filter) for fallback
        fallback_perm = None
        fallback_cost = float("inf")

        for perm in permutations(candidates):
            sorted_perm = sorted(perm)
            # Cost: pair voices by position (zip shortest)
            cost = sum(
                abs(s - t)
                for s, t in zip(source_sorted[:n_target], sorted_perm[:n_source])
            )

            # Track fallback (minimum cost regardless of parallels)
            if cost < fallback_cost:
                fallback_cost = cost
                fallback_perm = sorted_perm

            # Check for parallel 5ths/octaves (only when same number of voices)
            if n_source == n_target:
                if not _has_parallel_motion(source_sorted, sorted_perm):
                    if cost < best_cost:
                        best_cost = cost
                        best_perm = sorted_perm
            else:
                # Different sizes: no parallel check possible, use cost directly
                if cost < best_cost:
                    best_cost = cost
                    best_perm = sorted_perm

        # Fallback: if all permutations had parallels, use minimum cost
        if best_perm is None:
            best_perm = fallback_perm
    else:
        # Large chords (>5 notes): use sorted candidates directly
        best_perm = sorted(candidates)

    return [_make_note_obj(_midi_to_pitch(m)) for m in best_perm]


def voice_lead_progression(key, numerals, scale_type="major", octave=4):
    """Generate a voice-led chord progression with parallel 5ths/octaves avoidance.

    Resolves each Roman numeral to a chord, then applies voice_lead_chords()
    between consecutive chords for smooth voice leading.

    Args:
        key: Key root note (e.g., "C", "G", "F#").
        numerals: List of Roman numeral strings (e.g., ["I", "IV", "V", "I"]).
        scale_type: Scale/mode for chord resolution (default "major").
        octave: Target octave for chord voicings (default 4).

    Returns:
        dict: {"key": str, "scale_type": str,
               "chords": [{"numeral": str, "root": str, "quality": str,
                           "notes": [{"midi": int, "name": str}, ...]}, ...]}

    Raises:
        ValueError: If numerals is empty.
    """
    if not numerals:
        raise ValueError("numerals must be a non-empty list of Roman numeral strings")

    chords = []

    # First chord: use as-is from resolution
    first_chord = _resolve_numeral_to_chord(numerals[0], key, scale_type, octave)
    chords.append(first_chord)

    # Subsequent chords: voice-lead from previous
    for i in range(1, len(numerals)):
        next_chord_raw = _resolve_numeral_to_chord(numerals[i], key, scale_type, octave)

        # Extract MIDI pitches
        prev_midis = [n["midi"] for n in chords[-1]["notes"]]
        curr_midis = [n["midi"] for n in next_chord_raw["notes"]]

        # Apply voice leading with parallel avoidance
        voiced_notes = voice_lead_chords(prev_midis, curr_midis)

        chords.append({
            "numeral": numerals[i],
            "root": next_chord_raw["root"],
            "quality": next_chord_raw["quality"],
            "notes": voiced_notes,
        })

    return {
        "key": key,
        "scale_type": scale_type,
        "chords": chords,
    }
