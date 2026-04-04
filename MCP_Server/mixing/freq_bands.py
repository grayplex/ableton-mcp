"""Frequency band definitions and conflict detection logic for section-aware mixing.

Provides standard mixing frequency bands, role-to-band mappings, and functions
to detect frequency masking conflicts between tracks based on EQ settings.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Standard mixing frequency bands: name -> (low_hz, high_hz)
FREQ_BANDS: Dict[str, Tuple[int, int]] = {
    "sub": (20, 60),
    "low": (60, 250),
    "low_mid": (250, 500),
    "mid": (500, 2000),
    "upper_mid": (2000, 4000),
    "presence": (4000, 6000),
    "brilliance": (6000, 20000),
}

# Each role's primary frequency bands (where it should dominate)
ROLE_PRIMARY_BANDS: Dict[str, List[str]] = {
    "kick": ["sub", "low"],
    "bass": ["sub", "low", "low_mid"],
    "lead": ["mid", "upper_mid"],
    "pad": ["low_mid", "mid"],
    "chords": ["low_mid", "mid", "upper_mid"],
    "vocal": ["mid", "upper_mid", "presence"],
    "atmospheric": ["presence", "brilliance"],
}


def _freq_to_band(frequency: float) -> Optional[str]:
    """Map a frequency in Hz to its band name. Returns None if out of range."""
    for band_name, (low, high) in FREQ_BANDS.items():
        if low <= frequency < high:
            return band_name
    # Edge case: 20000 Hz falls in brilliance
    if frequency >= 20000:
        return "brilliance"
    return None


def extract_eq_bands(recipe_or_params: dict) -> List[dict]:
    """Parse Eq8 filter data from a recipe dict or live device params.

    Looks for Eq8 key in the dict. For each numbered band (1-8), extracts
    frequency and gain if gain is non-zero.

    Args:
        recipe_or_params: Dict that may contain an "Eq8" key with param values.

    Returns:
        List of {"frequency": float, "gain": float} for active bands with non-zero gain.
    """
    eq8_data = recipe_or_params.get("Eq8")
    if eq8_data is None:
        return []

    bands = []
    for band_num in range(1, 9):
        freq_key = f"{band_num} Frequency A"
        gain_key = f"{band_num} Gain A"
        freq = eq8_data.get(freq_key)
        gain = eq8_data.get(gain_key)
        if freq is not None and gain is not None and gain != 0.0:
            bands.append({"frequency": float(freq), "gain": float(gain)})

    return bands


def detect_conflicts(tracks: List[dict]) -> List[dict]:
    """Detect frequency masking conflicts between tracks.

    Args:
        tracks: List of {"name": str, "role": str | None, "eq_bands": list[dict]}
                where eq_bands items have "frequency" and "gain" keys.

    Returns:
        List of conflict dicts:
        {"band": str, "freq_range": [int, int], "tracks": [str],
         "severity": "high"|"medium", "suggestion": str}

    Severity rules:
    - HIGH: 2+ tracks boost the same band AND neither has that band as primary
    - MEDIUM: 2+ tracks boost the same band AND at least one has it as primary
    """
    # Build a map: band_name -> list of (track_name, role, gain) that boost in that band
    band_boosters: Dict[str, List[Tuple[str, Optional[str], float]]] = {
        band: [] for band in FREQ_BANDS
    }

    for track in tracks:
        name = track["name"]
        role = track.get("role")
        eq_bands = track.get("eq_bands", [])

        for eq in eq_bands:
            freq = eq.get("frequency", 0)
            gain = eq.get("gain", 0)
            if gain <= 0:
                continue  # Only boosts cause masking

            band = _freq_to_band(freq)
            if band is not None:
                band_boosters[band].append((name, role, gain))

    conflicts = []
    for band_name, boosters in band_boosters.items():
        if len(boosters) < 2:
            continue

        track_names = [b[0] for b in boosters]
        roles = [b[1] for b in boosters]
        freq_range = list(FREQ_BANDS[band_name])

        # Determine severity based on primary bands
        any_has_primary = False
        non_primary_tracks = []
        for track_name, role, _gain in boosters:
            primary = ROLE_PRIMARY_BANDS.get(role, []) if role else []
            if band_name in primary:
                any_has_primary = True
            else:
                non_primary_tracks.append(track_name)

        if any_has_primary:
            severity = "medium"
            # Suggestion targets the non-primary tracks
            if non_primary_tracks:
                target = non_primary_tracks[0]
                mid_freq = (freq_range[0] + freq_range[1]) // 2
                suggestion = (
                    f"Cut {target} EQ at {mid_freq} Hz to reduce masking "
                    f"with {', '.join(t for t in track_names if t != target)} in {band_name} band"
                )
            else:
                # All tracks have this as primary - still medium
                suggestion = (
                    f"Both {' and '.join(track_names)} claim {band_name} band as primary - "
                    f"use EQ to carve space between {freq_range[0]}-{freq_range[1]} Hz"
                )
        else:
            severity = "high"
            mid_freq = (freq_range[0] + freq_range[1]) // 2
            suggestion = (
                f"Cut {track_names[0]} EQ at {mid_freq} Hz to reduce masking "
                f"with {', '.join(track_names[1:])} in {band_name} band"
            )

        conflicts.append({
            "band": band_name,
            "freq_range": freq_range,
            "tracks": track_names,
            "severity": severity,
            "suggestion": suggestion,
        })

    return conflicts
