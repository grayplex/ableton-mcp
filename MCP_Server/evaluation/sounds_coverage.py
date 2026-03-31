"""Sound selection coverage evaluator.

evaluate_sounds_coverage(conn) -> DimensionScore

Checks that each instrument-loaded track has an instrument matching
the expected role descriptor profile from the sounds/ package.

Per D-04: Matches on device_name (display name), not class_name.
Per D-05: Pre-builds role->instrument map from catalog at call time.
"""

from MCP_Server.devices.catalog import ROLES
from MCP_Server.evaluation.schema import DimensionScore, EvaluationIssue, grade_from_score
from MCP_Server.sounds.catalog import get_profile, list_profiles


def _infer_role(track_name: str) -> str | None:
    """Infer mixing role from track name via case-insensitive substring match."""
    name_lower = track_name.lower()
    for role in ROLES:
        if role in name_lower:
            return role
    return None


def _build_role_to_instrument() -> dict[str, str]:
    """Build a mapping from role tag to the best-matched instrument name.

    For each role, finds the instrument with the highest role affinity weight.
    Returns: {role_tag -> instrument_display_name}
    """
    role_best: dict[str, tuple[float, str]] = {}  # role -> (best_score, instrument_name)

    for profile_meta in list_profiles():
        profile = get_profile(profile_meta["id"])
        if profile is None:
            continue

        name = profile["name"]
        role_affinities = profile.get("descriptor_affinities", {}).get("role", {})

        for role_tag, weight in role_affinities.items():
            current = role_best.get(role_tag, (0.0, ""))
            if weight > current[0]:
                role_best[role_tag] = (weight, name)

    return {role: name for role, (_, name) in role_best.items()}


def evaluate_sounds_coverage(conn) -> DimensionScore:
    """Evaluate sound selection coverage.

    Args:
        conn: Ableton connection -- must support .send_command(cmd, args).

    Returns:
        DimensionScore with score 0-10, grade, and list of EvaluationIssue.
    """
    mix_state = conn.send_command("get_mix_state", {})
    role_to_instrument = _build_role_to_instrument()

    issues: list[EvaluationIssue] = []
    total_checked = 0
    matched = 0

    all_tracks = list(mix_state.get("tracks", []))

    for track in all_tracks:
        track_name = track["name"]
        role = _infer_role(track_name)
        if role is None:
            continue  # Unknown role -- skip

        devices = track.get("devices", [])
        if not devices:
            continue  # No instruments loaded -- skip (arrangement evaluator handles this)

        expected_instrument = role_to_instrument.get(role)
        if expected_instrument is None:
            continue  # No profile maps to this role -- skip

        total_checked += 1

        # Check if any loaded device name matches the expected instrument
        device_names = [d.get("device_name", "") for d in devices]
        match_found = any(
            expected_instrument.lower() in dn.lower() for dn in device_names
        )

        if match_found:
            matched += 1
        else:
            loaded_names = ", ".join(n for n in device_names if n)
            issues.append(EvaluationIssue(
                dimension="sounds",
                severity="warning",
                message=(
                    f"'{track_name}' ({role}): loaded '{loaded_names}' "
                    f"but '{expected_instrument}' is the top-affinity instrument for {role} role"
                ),
                fix_hint=(
                    f"get_sound_recommendation(descriptor='{role}') "
                    f"then load_instrument_or_effect on '{track_name}'"
                ),
            ))

    if total_checked == 0:
        # No tracks with known roles and instruments -- nothing to evaluate
        score = 10.0
    else:
        score = round((matched / total_checked) * 10.0, 2)

    return DimensionScore(
        dimension="sounds",
        score=score,
        grade=grade_from_score(score),
        issues=issues,
    )
