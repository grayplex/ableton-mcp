"""Harmonic coherence evaluator.

evaluate_harmonic(conn) -> DimensionScore

Checks that MIDI notes in Session view clips fit within the session's
key and scale. Out-of-key notes are flagged with track name, clip info,
and MIDI pitch.

Per D-06: If no scale set (scale_name empty), returns score=10.0 with info issue.
Per D-07: Pitch classes computed from root_note + scale_intervals (no music21).
Per D-08: Iterates Session view clips via get_session_state + get_notes.
Per D-09: score = (in_key_notes / total_notes) * 10; 0 notes -> 10.0.
"""

from MCP_Server.evaluation.schema import DimensionScore, EvaluationIssue, grade_from_score


def _compute_pitch_classes(root_note: int, scale_intervals: list[int]) -> set[int]:
    """Compute the set of in-key pitch classes (0-11) from root + intervals.

    Args:
        root_note: Root note as integer 0-11 (C=0, C#=1, ..., B=11).
        scale_intervals: List of semitone intervals between consecutive scale degrees.

    Returns:
        Set of pitch class integers (0-11) that are in the scale.
    """
    pitch_classes: set[int] = set()
    cumulative = 0
    pitch_classes.add(root_note % 12)
    for interval in scale_intervals:
        cumulative += interval
        pitch_classes.add((root_note + cumulative) % 12)
    return pitch_classes


def evaluate_harmonic(conn) -> DimensionScore:
    """Evaluate harmonic coherence: check MIDI notes against session key/scale.

    Args:
        conn: Ableton connection -- must support .send_command(cmd, args).

    Returns:
        DimensionScore with score 0-10, grade, and list of EvaluationIssue.
    """
    scale_info = conn.send_command("get_scale_info", {})
    scale_name = scale_info.get("scale_name", "")
    scale_intervals = scale_info.get("scale_intervals", [])
    root_note = scale_info.get("root_note", 0)

    # D-06: No key set -- skip evaluation with info issue
    if not scale_name or not scale_intervals:
        return DimensionScore(
            dimension="harmony",
            score=10.0,
            grade="A",
            issues=[EvaluationIssue(
                dimension="harmony",
                severity="info",
                message="No session key set -- harmonic coherence check skipped",
                fix_hint="set_scale(root_note=0, scale_name='major') to enable harmonic evaluation",
            )],
        )

    pitch_classes = _compute_pitch_classes(root_note, scale_intervals)

    # Get session state for track + clip list
    session_state = conn.send_command("get_session_state", {})
    tracks = session_state.get("tracks", [])

    issues: list[EvaluationIssue] = []
    total_notes = 0
    in_key_notes = 0

    for track in tracks:
        track_name = track["name"]
        track_index = track.get("index", 0)
        clips = track.get("clips", [])

        for clip in clips:
            scene_index = clip["scene_index"]
            clip_name = clip.get("name", f"clip_{scene_index}")

            try:
                note_data = conn.send_command(
                    "get_notes",
                    {"track_index": track_index, "clip_index": scene_index},
                )
                notes = note_data.get("notes", [])
            except Exception:
                continue  # Clip not accessible -- skip silently

            for note in notes:
                pitch = note.get("pitch", 0)
                total_notes += 1
                if pitch % 12 in pitch_classes:
                    in_key_notes += 1
                else:
                    start_time = note.get("start_time", 0.0)
                    issues.append(EvaluationIssue(
                        dimension="harmony",
                        severity="warning",
                        message=(
                            f"'{track_name}' / '{clip_name}': "
                            f"note pitch {pitch} (beat {start_time:.2f}) "
                            f"is outside {scale_name} scale"
                        ),
                        fix_hint=(
                            f"get_notes(track_index={track_index}, clip_index={scene_index}) "
                            f"then remove_notes or transpose out-of-key notes"
                        ),
                    ))

    # D-09: score formula
    if total_notes == 0:
        score = 10.0
    else:
        score = round((in_key_notes / total_notes) * 10.0, 2)

    return DimensionScore(
        dimension="harmony",
        score=score,
        grade=grade_from_score(score),
        issues=issues,
    )
