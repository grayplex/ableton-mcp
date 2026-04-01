"""Arrangement completeness evaluator.

evaluate_arrangement(conn) -> DimensionScore

Checks that every regular track has:
(a) an instrument loaded (has_instrument) -- missing instrument is CRITICAL
(b) at least one arrangement clip placed -- no clips with instrument is WARNING

Per D-01: Uses get_arrangement_state + get_arrangement_clips per track.
Per D-02: Only regular tracks (not return/master).
Per D-03: score = weighted clean_track_fraction * 10.
"""

from MCP_Server.evaluation.schema import DimensionScore, EvaluationIssue, grade_from_score


def evaluate_arrangement(conn) -> DimensionScore:
    """Evaluate arrangement completeness.

    Args:
        conn: Ableton connection -- must support .send_command(cmd, args).

    Returns:
        DimensionScore with score 0-10, grade, and list of EvaluationIssue.
    """
    arrangement_state = conn.send_command("get_arrangement_state", {})
    tracks = arrangement_state.get("tracks", [])

    if not tracks:
        return DimensionScore(
            dimension="arrangement",
            score=10.0,
            grade="A",
            issues=[],
        )

    issues: list[EvaluationIssue] = []
    weighted_clean = 0.0

    for i, track in enumerate(tracks):
        track_name = track["name"]
        has_instrument = track.get("has_instrument", False)

        if not has_instrument:
            issues.append(EvaluationIssue(
                dimension="arrangement",
                severity="critical",
                message=f"'{track_name}': no instrument loaded -- track will produce silence",
                fix_hint=f"load_instrument_or_effect(track_name='{track_name}', path='...')",
            ))
            # weighted_clean += 0 (critical)
            continue

        # Check for arrangement clips
        try:
            clip_data = conn.send_command("get_arrangement_clips", {"track_index": i})
            clips = clip_data.get("clips", [])
        except Exception:
            clips = []

        if not clips:
            issues.append(EvaluationIssue(
                dimension="arrangement",
                severity="warning",
                message=f"'{track_name}': instrument loaded but no arrangement clips placed",
                fix_hint=f"create_midi_clip_in_arrangement(track_index={i}, start_time=0.0, length=4.0)",
            ))
            weighted_clean += 0.5  # partial credit
        else:
            weighted_clean += 1.0  # fully clean

    total = len(tracks)
    score = round((weighted_clean / total) * 10.0, 2) if total > 0 else 10.0
    score = max(0.0, min(10.0, score))

    return DimensionScore(
        dimension="arrangement",
        score=score,
        grade=grade_from_score(score),
        issues=issues,
    )
