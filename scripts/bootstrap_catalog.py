"""Bootstrap script for generating the device parameter catalog from a live Ableton session.

Purpose:
    Queries a live Ableton Live session to get the real parameter names, value ranges,
    and quantization flags for each of the 12 target devices. Writes the result to
    MCP_Server/devices/catalog.py so the catalog is grounded in actual Ableton API data
    rather than hand-authored documentation.

    This fulfills the CATL-01 constraint: catalog entries MUST be validated against a
    live Ableton session.

Prerequisites:
    - Ableton Live is running with the AbletonMCP Remote Script loaded
    - A session is open with all 12 target devices loaded on tracks (one device per track
      is the simplest setup). The devices must be present somewhere in the session:
        EQ Eight, Compressor, Glue Compressor, Drum Buss, Multiband Dynamics,
        Reverb, Delay, Auto Filter, Gate, Limiter, Envelope Follower, Utility

Usage:
    python -m scripts.bootstrap_catalog

After running:
    - Review MCP_Server/devices/catalog.py and spot-check a few entries against
      the Ableton device parameter view.
    - Run: python -m pytest tests/test_catalog.py -x -q
    - Commit the updated catalog.py.
"""

from __future__ import annotations

import os
import pprint
import sys

# ---------------------------------------------------------------------------
# Target devices
# ---------------------------------------------------------------------------

TARGET_DEVICES = [
    "EQ Eight",
    "Compressor",
    "Glue Compressor",
    "Drum Buss",
    "Multiband Dynamics",
    "Reverb",
    "Delay",
    "Auto Filter",
    "Gate",
    "Limiter",
    "Envelope Follower",
    "Utility",
]

# ---------------------------------------------------------------------------
# Known conversion metadata (keyed by substring match on parameter name)
# ---------------------------------------------------------------------------
# The bootstrap captures raw normalized [0.0, 1.0] ranges from Ableton.
# Parameters that are stored internally as normalized values need a conversion
# dict so recipe code can work in natural units (Hz, dB, ms, %).
# Parameters that are already in natural units or are quantized on/off toggles
# keep conversion=None.
#
# Match rule: if any KNOWN_CONVERSIONS key is a substring of the parameter name,
# that conversion is applied. First match wins.

KNOWN_CONVERSIONS: dict[str, dict] = {
    # EQ frequency parameters
    "Frequency": {"type": "log", "natural_min": 20, "natural_max": 22050, "unit": "Hz"},
    # EQ/Compressor gain parameters
    "Gain": {"type": "linear_db", "natural_min": -15, "natural_max": 15, "unit": "dB"},
    # Threshold parameters
    "Threshold": {"type": "linear_db", "natural_min": -40, "natural_max": 0, "unit": "dB"},
    # Attack/Release time parameters
    "Attack": {"type": "log", "natural_min": 0.01, "natural_max": 1000, "unit": "ms"},
    "Release": {"type": "log", "natural_min": 0.01, "natural_max": 3000, "unit": "ms"},
    # Dry/Wet parameters
    "Dry/Wet": {"type": "linear", "natural_min": 0, "natural_max": 100, "unit": "%"},
    # Output/Volume/Makeup gain
    "Output Gain": {"type": "linear_db", "natural_min": -36, "natural_max": 36, "unit": "dB"},
    "Makeup": {"type": "linear_db", "natural_min": -15, "natural_max": 15, "unit": "dB"},
}

# Canonical roles list -- preserved when catalog.py is regenerated
ROLES = [
    "kick", "bass", "lead", "pad",
    "chords", "vocal", "atmospheric",
    "return", "master",
]

# Output path (relative to project root, i.e. where this script is run from)
CATALOG_OUTPUT_PATH = "MCP_Server/devices/catalog.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def match_conversion(param_name: str) -> dict | None:
    """Return the conversion dict for param_name, or None if no pattern matches.

    Checks each key in KNOWN_CONVERSIONS as a substring of param_name.
    Returns a copy of the first matching conversion dict, or None.
    """
    for pattern, conversion in KNOWN_CONVERSIONS.items():
        if pattern in param_name:
            return dict(conversion)
    return None


def _build_catalog_entry(class_name: str, device_name: str, parameters: list[dict]) -> dict:
    """Build a single CATALOG entry from raw Ableton parameter data."""
    param_entries = []
    for p in parameters:
        entry = {
            "name": p["name"],
            "index": p["index"],
            "min": p["min"],
            "max": p["max"],
            "is_quantized": p["is_quantized"],
            "conversion": match_conversion(p["name"]) if not p.get("is_quantized") else None,
        }
        param_entries.append(entry)
    return {
        "display_name": device_name,
        "parameters": param_entries,
    }


# ---------------------------------------------------------------------------
# Bootstrap entry point
# ---------------------------------------------------------------------------

def bootstrap() -> None:
    """Connect to live Ableton, query all 12 target devices, write catalog.py."""
    from MCP_Server.connection import get_ableton_connection

    print("Connecting to Ableton Live...")
    try:
        ableton = get_ableton_connection()
    except Exception as exc:
        print(
            f"\nError: Could not connect to Ableton Live.\n"
            f"Detail: {exc}\n\n"
            "Ensure the AbletonMCP Remote Script is loaded and Ableton is running.\n"
            "Check that Ableton's Remote Script socket is listening on localhost:9877."
        )
        sys.exit(1)

    print("Connected. Fetching session info...")
    try:
        session = ableton.send_command("get_session_info")
    except Exception as exc:
        print(f"Error: Could not get session info: {exc}")
        sys.exit(1)

    tracks = session.get("tracks", [])
    print(f"Session has {len(tracks)} tracks. Scanning for target devices...")

    # Build a case-insensitive lookup from display name -> class_name + params
    found: dict[str, dict] = {}  # display_name -> catalog entry dict

    for track_idx, track in enumerate(tracks):
        device_count = track.get("num_devices", 0)
        for device_idx in range(device_count):
            try:
                result = ableton.send_command("get_device_parameters",
                    {"track_index": track_idx, "device_index": device_idx},
                )
            except Exception as exc:
                print(
                    f"  Warning: Could not query track {track_idx} device {device_idx}: {exc}"
                )
                continue

            device_name = result.get("device_name", "")
            class_name = result.get("class_name", "")
            parameters = result.get("parameters", [])

            if device_name in TARGET_DEVICES and device_name not in found:
                print(
                    f"  Found '{device_name}' (class={class_name}) "
                    f"with {len(parameters)} parameters on track {track_idx}"
                )
                found[device_name] = (class_name, device_name, parameters)

    # Validate all 12 devices were found
    missing = [d for d in TARGET_DEVICES if d not in found]
    if missing:
        print(
            f"\nError: The following devices were not found in the current session:\n"
            + "\n".join(f"  - {d}" for d in missing)
            + "\n\nPlease load all 12 target devices on tracks in Ableton and re-run.\n"
            "Tip: Create 12 audio tracks and drop one target device on each."
        )
        sys.exit(1)

    # Build CATALOG dict in TARGET_DEVICES order (deterministic output)
    catalog: dict[str, dict] = {}
    total_params = 0
    for display_name in TARGET_DEVICES:
        class_name, dev_name, parameters = found[display_name]
        catalog[class_name] = _build_catalog_entry(class_name, dev_name, parameters)
        total_params += len(parameters)

    # Read existing catalog.py to preserve ROLES if present (fallback to module ROLES)
    existing_roles = ROLES
    if os.path.exists(CATALOG_OUTPUT_PATH):
        try:
            with open(CATALOG_OUTPUT_PATH, "r", encoding="utf-8") as f:
                src = f.read()
            # Simple extraction: find ROLES = [...] line
            import re
            roles_match = re.search(r'^ROLES\s*=\s*(\[.*?\])', src, re.MULTILINE | re.DOTALL)
            if roles_match:
                existing_roles = eval(roles_match.group(1))  # noqa: S307 -- trusted file
        except Exception:
            pass  # Fall back to module ROLES constant

    # Write catalog.py
    catalog_repr = pprint.pformat(catalog, indent=4, width=100)
    roles_repr = repr(existing_roles)

    output = (
        "# Generated by scripts/bootstrap_catalog.py -- do not edit manually\n"
        "\n"
        f"CATALOG = {catalog_repr}\n"
        "\n"
        f"ROLES = {roles_repr}\n"
    )

    with open(CATALOG_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(output)

    print(
        f"\nCatalog written to {CATALOG_OUTPUT_PATH} with {len(catalog)} devices "
        f"and {total_params} parameters."
    )
    print("\nNext steps:")
    print("  1. Spot-check a few entries in MCP_Server/devices/catalog.py against Ableton's UI")
    print("  2. Run: python -m pytest tests/test_catalog.py -x -q")
    print("  3. Commit the updated catalog.py")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        bootstrap()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
    except Exception as exc:
        print(
            f"\nUnexpected error: {exc}\n"
            "Could not connect to Ableton Live. Ensure the Remote Script is loaded "
            "and Ableton is running."
        )
        sys.exit(1)
