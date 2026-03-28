"""Convert natural-unit recipe values to normalized 0.0-1.0 device parameters.

Per D-03: Conversion happens on the MCP side before sending to the Remote Script.
The RS handler receives already-normalized values and sets them directly.

Conversion types (from CATALOG):
- log: log(value/natural_min) / log(natural_max/natural_min)
- linear / linear_db: (value - natural_min) / (natural_max - natural_min)
- None: value is already in device range [min, max]; clamp and return
"""

import math
from typing import Dict, List

from MCP_Server.devices.catalog import CATALOG


def natural_to_normalized(
    device_class: str, param_name: str, natural_value: float
) -> float:
    """Convert a natural-unit value to the normalized device parameter range.

    Args:
        device_class: CATALOG key (e.g. "Eq8", "Compressor2").
        param_name: Parameter name as it appears in CATALOG.
        natural_value: Value in natural units (Hz, dB, ms, etc.).

    Returns:
        Normalized float. For unknown device/param, returns natural_value unchanged.
    """
    device_entry = CATALOG.get(device_class)
    if device_entry is None:
        return float(natural_value)

    # Find the parameter entry
    param_info = None
    for p in device_entry["parameters"]:
        if p["name"] == param_name:
            param_info = p
            break

    if param_info is None:
        return float(natural_value)

    conv = param_info.get("conversion")

    if conv is None:
        # No conversion -- clamp to device range and return
        clamped = max(param_info["min"], min(param_info["max"], float(natural_value)))
        return clamped

    natural_min = conv["natural_min"]
    natural_max = conv["natural_max"]
    conv_type = conv["type"]

    if conv_type == "log":
        # Defensive: avoid log(0)
        safe_min = natural_min if natural_min > 0 else 1e-10
        clamped = max(safe_min, min(natural_max, float(natural_value)))
        return math.log(clamped / safe_min) / math.log(natural_max / safe_min)

    if conv_type in ("linear", "linear_db"):
        clamped = max(natural_min, min(natural_max, float(natural_value)))
        span = natural_max - natural_min
        if span == 0:
            return 0.0
        return (clamped - natural_min) / span

    # Unknown conversion type -- return unchanged
    return float(natural_value)


def convert_recipe_to_payload(recipe: Dict[str, Dict[str, float]]) -> List[dict]:
    """Transform a recipe dict into normalized RS payload format.

    Args:
        recipe: {device_class: {param_name: natural_value, ...}, ...}

    Returns:
        List of {"class_name": str, "params": {param_name: normalized_value, ...}}
    """
    payload = []
    for device_class, params in recipe.items():
        normalized_params = {}
        for param_name, natural_value in params.items():
            normalized_params[param_name] = natural_to_normalized(
                device_class, param_name, natural_value
            )
        payload.append({"class_name": device_class, "params": normalized_params})
    return payload
