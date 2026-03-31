"""Mix balance evaluator: compare current device params vs. role x genre recipe targets.

evaluate_mix_balance(genre, conn) -> DimensionScore

Reuses:
- DIFF_THRESHOLD from tools/intelligence.py (0.03 normalized units)
- _infer_role() logic from tools/analysis.py
- natural_to_normalized() from devices/convert.py
- GAIN_TARGETS from devices/gain_targets.py
- get_recipe() from mixing/catalog.py

Per D-04: genre is required; without it recipe comparison is not possible.
Per D-05: score = (in_range_params / total_params) * 10; gain deviations subtract 0.5 each.
Per D-06: |delta| >= 0.15 -> critical; 0.03..0.15 -> warning; gain too_hot/too_quiet -> warning.
Per D-08: tracks with no devices skip param comparison; MIDI scaffold tracks with no
          instrument skip entirely.
"""

import math

from MCP_Server.devices.catalog import ROLES
from MCP_Server.devices.convert import natural_to_normalized
from MCP_Server.devices.gain_targets import GAIN_TARGETS
from MCP_Server.evaluation.schema import DimensionScore, EvaluationIssue, grade_from_score
from MCP_Server.mixing.catalog import get_recipe

DIFF_THRESHOLD = 0.03
CRITICAL_THRESHOLD = 0.15


def _infer_role(track_name: str) -> str | None:
    """Infer mixing role from track name via case-insensitive substring match."""
    name_lower = track_name.lower()
    for role in ROLES:
        if role in name_lower:
            return role
    return None


def _meter_to_db(value: float) -> float | None:
    """Convert normalized 0.0-1.0 peak meter reading to dBFS."""
    if value <= 0.0:
        return None
    return 20.0 * math.log10(value)


def _is_scaffold_no_instrument(track: dict) -> bool:
    """Return True if this is an empty MIDI scaffold track (no devices at all).

    Per D-08: tracks with no devices are skipped entirely.
    This matches the GAIN-02 exclusion in analysis.py.
    """
    return len(track.get("devices", [])) == 0


def evaluate_mix_balance(genre: str, conn) -> DimensionScore:
    """Evaluate mix balance: compare device params vs. role x genre recipe targets.

    Args:
        genre: Genre ID for recipe lookup (e.g. "house", "techno").
        conn: Ableton connection -- must support .send_command(cmd, args).

    Returns:
        DimensionScore with score 0-10, grade, and list of EvaluationIssue.
    """
    mix_state = conn.send_command("get_mix_state", {})
    meter_state = conn.send_command("get_track_meters", {})

    # Build meter lookup: track_name -> meter_level
    meter_lookup: dict[str, float] = {}
    for group_key in ("tracks", "return_tracks"):
        for t in meter_state.get(group_key, []):
            meter_lookup[t["name"]] = t.get("meter_level", 0.0)
    master = meter_state.get("master_track")
    if master:
        meter_lookup[master["name"]] = master.get("meter_level", 0.0)

    issues: list[EvaluationIssue] = []
    total_params = 0
    in_range_params = 0
    gain_deductions = 0

    all_tracks = list(mix_state.get("tracks", []))
    all_tracks += list(mix_state.get("return_tracks", []))
    mt = mix_state.get("master_track")
    if mt:
        all_tracks.append(mt)

    for track in all_tracks:
        track_name = track["name"]
        role = _infer_role(track_name)

        # Skip tracks with no role match (D-08: unknown role excluded from scoring)
        if role is None:
            continue

        # Skip empty scaffold tracks (D-08)
        if _is_scaffold_no_instrument(track):
            continue

        # ---- Gain staging check (always run, no recipe needed) ----
        meter_level = meter_lookup.get(track_name, 0.0)
        meter_db = _meter_to_db(meter_level)
        if meter_db is None:
            # No signal -- track has devices (scaffold guard above ensures this)
            issues.append(EvaluationIssue(
                dimension="mix",
                severity="info",
                message=f"'{track_name}' ({role}): no meter signal -- play the session to check gain staging",
                fix_hint="check_gain_staging() -- ensure session is playing",
            ))
        elif role in GAIN_TARGETS:
            lo, hi = GAIN_TARGETS[role]
            db_rounded = round(meter_db, 1)
            if db_rounded < lo:
                gain_deductions += 1
                issues.append(EvaluationIssue(
                    dimension="mix",
                    severity="warning",
                    message=f"'{track_name}' ({role}): gain too quiet at {db_rounded:.1f} dBFS (target {lo}..{hi} dBFS)",
                    fix_hint=f"Increase volume on '{track_name}' to reach {lo}..{hi} dBFS",
                ))
            elif db_rounded > hi:
                gain_deductions += 1
                issues.append(EvaluationIssue(
                    dimension="mix",
                    severity="warning",
                    message=f"'{track_name}' ({role}): gain too hot at {db_rounded:.1f} dBFS (target {lo}..{hi} dBFS)",
                    fix_hint=f"Reduce volume on '{track_name}' to reach {lo}..{hi} dBFS",
                ))

        # ---- Device parameter comparison vs. recipe ----
        recipe = get_recipe(role, genre)
        if recipe is None:
            continue  # No recipe for this role x genre -- skip param comparison

        # Build device param lookup: class_name -> {param_name: normalized_value}
        track_devices: dict[str, dict[str, float]] = {}
        for dev in track.get("devices", []):
            params = {p["name"]: p["value"] for p in dev.get("parameters", [])}
            track_devices[dev["class_name"]] = params

        for device_class, recipe_params in recipe.items():
            if device_class not in track_devices:
                continue  # Device not loaded -- skip silently (same as intelligence.py D-04)

            current_params = track_devices[device_class]
            for param_name, recipe_natural in recipe_params.items():
                if param_name not in current_params:
                    continue

                current_norm = current_params[param_name]
                suggested_norm = natural_to_normalized(device_class, param_name, recipe_natural)
                delta = abs(current_norm - suggested_norm)

                total_params += 1
                if delta < DIFF_THRESHOLD:
                    in_range_params += 1
                else:
                    severity = "critical" if delta >= CRITICAL_THRESHOLD else "warning"
                    issues.append(EvaluationIssue(
                        dimension="mix",
                        severity=severity,
                        message=(
                            f"'{track_name}' ({role}): {device_class}.{param_name} "
                            f"deviates from {genre} recipe by {delta:.3f} normalized units"
                        ),
                        fix_hint=(
                            f"apply_mix_recipe(track_name='{track_name}', "
                            f"genre='{genre}', role='{role}')"
                        ),
                    ))

    # ---- Compute score ----
    if total_params > 0:
        param_score = (in_range_params / total_params) * 10.0
    else:
        param_score = 10.0  # No recipe params to compare -- assume perfect

    # Each gain deviation deducts 0.5, clamped to 0.0
    score = max(0.0, param_score - (gain_deductions * 0.5))
    score = round(score, 2)

    return DimensionScore(
        dimension="mix",
        score=score,
        grade=grade_from_score(score),
        issues=issues,
    )
