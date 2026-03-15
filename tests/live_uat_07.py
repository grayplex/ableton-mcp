"""Live UAT tests for Phase 7: Device & Browser against running Ableton instance."""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from MCP_Server.connection import AbletonConnection


def connect():
    conn = AbletonConnection(host="localhost", port=9877)
    if not conn.connect():
        print("FAIL: Could not connect to Ableton. Is the Remote Script running?")
        sys.exit(1)
    return conn


def _ensure_track_with_device(conn):
    """Helper: Create a MIDI track and load an instrument. Returns (track_idx, cleanup_fn)."""
    create_result = conn.send_command("create_midi_track", {"name": "UAT-DeviceTest"})
    track_idx = create_result.get("index")

    # Browse for a loadable instrument
    browse = conn.send_command("get_browser_tree", {
        "category_type": "instruments",
        "max_depth": 2,
    })
    uri = None
    for cat in browse.get("categories", []):
        for child in cat.get("children", []):
            if child.get("is_loadable"):
                uri = child.get("uri")
                break
            for sub in child.get("children", []):
                if sub.get("is_loadable"):
                    uri = sub.get("uri")
                    break
            if uri:
                break
        if uri:
            break

    if not uri:
        conn.send_command("delete_track", {"track_index": track_idx})
        return None, None

    conn.send_command("load_instrument_or_effect", {
        "track_index": track_idx,
        "item_uri": uri,
    })

    def cleanup():
        try:
            conn.send_command("delete_track", {"track_index": track_idx})
        except Exception:
            pass

    return track_idx, cleanup


def test_get_device_parameters(conn):
    """Test 1: Get Device Parameters"""
    track_idx, cleanup = _ensure_track_with_device(conn)
    if track_idx is None:
        return "skip", "Could not create track with device"

    try:
        result = conn.send_command("get_device_parameters", {
            "track_index": track_idx,
            "device_index": 0,
        })
    except Exception as e:
        cleanup()
        return "issue", f"get_device_parameters failed: {e}"

    cleanup()

    if "device_name" not in result:
        return "issue", f"Response missing device_name: {json.dumps(result)[:200]}"
    if "parameters" not in result:
        return "issue", f"Response missing parameters key: {json.dumps(result)[:200]}"
    if not isinstance(result["parameters"], list):
        return "issue", f"Parameters is not a list: {type(result['parameters'])}"

    params = result["parameters"]
    if len(params) > 0:
        p = params[0]
        required_keys = {"name", "value", "min", "max"}
        missing = required_keys - set(p.keys())
        if missing:
            return "issue", f"Parameter missing keys: {missing}"

    return "pass", f"Got {len(params)} params for '{result['device_name']}' on track {track_idx}"


def test_set_device_parameter_by_name(conn):
    """Test 2: Set Device Parameter by Name"""
    track_idx, cleanup = _ensure_track_with_device(conn)
    if track_idx is None:
        return "skip", "Could not create track with device"

    try:
        # Get params first
        params_result = conn.send_command("get_device_parameters", {
            "track_index": track_idx,
            "device_index": 0,
        })
        params = params_result.get("parameters", [])
    except Exception as e:
        cleanup()
        return "issue", f"get_device_parameters failed: {e}"

    # Find a non-quantized parameter to adjust
    target_param = None
    for p in params:
        if not p.get("is_quantized", True) and p["min"] != p["max"]:
            target_param = p
            break

    if target_param is None:
        for p in params:
            if p["min"] != p["max"]:
                target_param = p
                break

    if target_param is None:
        cleanup()
        return "skip", "No adjustable parameters found"

    # Set to midpoint
    mid = (target_param["min"] + target_param["max"]) / 2
    try:
        result = conn.send_command("set_device_parameter", {
            "track_index": track_idx,
            "device_index": 0,
            "parameter_name": target_param["name"],
            "value": mid,
        })
    except Exception as e:
        cleanup()
        return "issue", f"set_device_parameter failed: {e}"

    cleanup()

    if "parameter_name" not in result and "value" not in result:
        return "issue", f"Response missing expected keys: {json.dumps(result)[:200]}"

    return "pass", f"Set '{target_param['name']}' to {mid} on track {track_idx}"


def test_delete_device(conn):
    """Test 3: Delete a Device"""
    # Create a fresh MIDI track, load an instrument, then delete it
    create_result = conn.send_command("create_midi_track", {"name": "UAT-DeleteTest"})
    track_idx = create_result.get("index")
    if track_idx is None:
        return "issue", f"Failed to create test track: {json.dumps(create_result)[:200]}"

    try:
        # Browse for a loadable instrument
        browse = conn.send_command("get_browser_tree", {
            "category_type": "instruments",
            "max_depth": 2,
        })
        uri = None
        for cat in browse.get("categories", []):
            for child in cat.get("children", []):
                if child.get("is_loadable"):
                    uri = child.get("uri")
                    break
                for sub in child.get("children", []):
                    if sub.get("is_loadable"):
                        uri = sub.get("uri")
                        break
                if uri:
                    break
            if uri:
                break

        if not uri:
            conn.send_command("delete_track", {"track_index": track_idx})
            return "skip", "No loadable instrument found"

        conn.send_command("load_instrument_or_effect", {
            "track_index": track_idx,
            "item_uri": uri,
        })
    except Exception as e:
        conn.send_command("delete_track", {"track_index": track_idx})
        return "issue", f"Could not load instrument for delete test: {e}"

    # Now get track info to verify device exists
    try:
        pre_info = conn.send_command("get_device_parameters", {
            "track_index": track_idx,
            "device_index": 0,
        })
        device_name = pre_info.get("device_name", "unknown")
    except Exception:
        device_name = "unknown"

    # Delete the device
    try:
        result = conn.send_command("delete_device", {
            "track_index": track_idx,
            "device_index": 0,
        })
    except Exception as e:
        conn.send_command("delete_track", {"track_index": track_idx})
        return "issue", f"delete_device failed: {e}"

    if "deleted_device_name" not in result:
        conn.send_command("delete_track", {"track_index": track_idx})
        return "issue", f"Response missing deleted_device_name: {json.dumps(result)[:200]}"

    # Cleanup
    conn.send_command("delete_track", {"track_index": track_idx})
    return "pass", f"Deleted '{result.get('deleted_device_name', device_name)}', updated devices: {result.get('updated_devices', [])}"


def test_get_rack_chains(conn):
    """Test 4: Get Rack Chains"""
    # Create a MIDI track and load an Instrument Rack
    create_result = conn.send_command("create_midi_track", {"name": "UAT-RackTest"})
    track_idx = create_result.get("index")
    if track_idx is None:
        return "issue", f"Failed to create test track: {json.dumps(create_result)[:200]}"

    # First browse to find a loadable instrument
    try:
        browse = conn.send_command("get_browser_tree", {
            "category_type": "instruments",
            "max_depth": 1,
        })
        categories = browse.get("categories", [])
        uri = None
        for cat in categories:
            for child in cat.get("children", []):
                if child.get("is_loadable"):
                    uri = child.get("uri")
                    break
            if uri:
                break

        if uri:
            conn.send_command("load_instrument_or_effect", {
                "track_index": track_idx,
                "item_uri": uri,
            })
        else:
            conn.send_command("delete_track", {"track_index": track_idx})
            return "skip", "No loadable instrument found in browser"
    except Exception as e:
        conn.send_command("delete_track", {"track_index": track_idx})
        return "skip", f"Could not browse/load instrument: {e}"

    # Check if the loaded device is a rack
    try:
        track_info = conn.send_command("get_track_info", {"track_index": track_idx})
        devices = track_info.get("devices", [])
        if not devices:
            conn.send_command("delete_track", {"track_index": track_idx})
            return "skip", "No devices on track after load"

        # Try get_rack_chains on device 0
        result = conn.send_command("get_rack_chains", {
            "track_index": track_idx,
            "device_index": 0,
        })
    except Exception as e:
        err = str(e)
        conn.send_command("delete_track", {"track_index": track_idx})
        if "not a rack" in err.lower() or "does not have chains" in err.lower():
            return "pass", f"Correctly rejects non-rack device: {err}"
        return "issue", f"get_rack_chains failed unexpectedly: {e}"

    conn.send_command("delete_track", {"track_index": track_idx})

    if "device_name" not in result:
        return "issue", f"Response missing device_name: {json.dumps(result)[:200]}"

    has_chains = "chains" in result or "pads" in result
    if not has_chains:
        return "issue", f"Response has neither 'chains' nor 'pads': {json.dumps(result)[:200]}"

    dtype = result.get("device_type", "unknown")
    chain_count = len(result.get("chains", result.get("pads", [])))
    return "pass", f"'{result['device_name']}' ({dtype}) has {chain_count} chains/pads"


def test_browse_with_depth(conn):
    """Test 5: Browse with Depth"""
    # Use audio_effects which is typically smaller than instruments
    result = conn.send_command("get_browser_tree", {
        "category_type": "audio_effects",
        "max_depth": 2,
    })

    categories = result.get("categories", [])
    if not categories:
        return "issue", f"No categories returned: {json.dumps(result)[:300]}"

    has_nested = False
    for cat in categories:
        for child in cat.get("children", []):
            if "children" in child and len(child.get("children", [])) > 0:
                has_nested = True
                break
        if has_nested:
            break

    if not has_nested:
        return "issue", "max_depth=2 returned no nested children in categories"

    total_children = sum(len(c.get("children", [])) for c in categories)
    return "pass", f"Got {len(categories)} categories with {total_children} children, nested at depth 2"


def test_load_instrument_by_path(conn):
    """Test 6: Load Instrument by Path"""
    create_result = conn.send_command("create_midi_track", {"name": "UAT-PathLoad"})
    track_idx = create_result.get("index")
    if track_idx is None:
        return "issue", f"Failed to create test track: {json.dumps(create_result)[:200]}"

    # First browse to find a valid instrument name to construct a path
    try:
        browse = conn.send_command("get_browser_tree", {
            "category_type": "instruments",
            "max_depth": 1,
        })
        # Find first child of instruments category to construct path
        inst_name = None
        for cat in browse.get("categories", []):
            for child in cat.get("children", []):
                if child.get("is_loadable"):
                    inst_name = child.get("name")
                    break
                elif child.get("is_folder"):
                    inst_name = child.get("name")
                    break
            if inst_name:
                break

        if not inst_name:
            conn.send_command("delete_track", {"track_index": track_idx})
            return "skip", "No instruments found in browser"

        path = f"instruments/{inst_name}"
        result = conn.send_command("load_instrument_or_effect", {
            "track_index": track_idx,
            "path": path,
        })
    except Exception as e:
        conn.send_command("delete_track", {"track_index": track_idx})
        return "issue", f"Path-based load failed with path '{path if 'path' in dir() else '?'}': {e}"

    conn.send_command("delete_track", {"track_index": track_idx})

    if not result.get("loaded"):
        return "issue", f"loaded is not True: {json.dumps(result)[:200]}"
    if "parameters" not in result:
        return "issue", f"Response missing parameters: {json.dumps(result)[:200]}"

    return "pass", f"Loaded '{result.get('item_name', '?')}' via path '{path}' with {len(result.get('parameters', []))} params"


def test_audio_track_load_guard(conn):
    """Test 7: Audio Track Load Guard"""
    create_result = conn.send_command("create_audio_track", {"name": "UAT-AudioGuard"})
    track_idx = create_result.get("index")
    if track_idx is None:
        return "issue", f"Failed to create audio track: {json.dumps(create_result)[:200]}"

    # Find an instrument URI to try loading
    try:
        browse = conn.send_command("get_browser_tree", {
            "category_type": "instruments",
            "max_depth": 2,
        })
        uri = None
        for cat in browse.get("categories", []):
            for child in cat.get("children", []):
                if child.get("is_loadable"):
                    uri = child.get("uri")
                    break
                for sub in child.get("children", []):
                    if sub.get("is_loadable"):
                        uri = sub.get("uri")
                        break
                if uri:
                    break
            if uri:
                break
    except Exception:
        uri = None

    if not uri:
        conn.send_command("delete_track", {"track_index": track_idx})
        return "skip", "No instrument URI found to test audio track guard"

    try:
        result = conn.send_command("load_instrument_or_effect", {
            "track_index": track_idx,
            "item_uri": uri,
        })
        # If we get here without error, the guard didn't work
        conn.send_command("delete_track", {"track_index": track_idx})
        return "issue", f"Expected error for instrument-on-audio-track but got success: {json.dumps(result)[:200]}"
    except Exception as e:
        error_msg = str(e)
        conn.send_command("delete_track", {"track_index": track_idx})
        if "audio track" in error_msg.lower() or "midi track" in error_msg.lower():
            return "pass", f"Guard triggered: {error_msg}"
        else:
            return "issue", f"Got error but not the expected guard message: {error_msg}"


def test_get_session_state(conn):
    """Test 8: Get Session State"""
    try:
        result = conn.send_command("get_session_state", {"detailed": False})
    except Exception as e:
        return "issue", f"get_session_state (lightweight) crashed: {e}"

    if "transport" not in result:
        return "issue", f"Response missing transport: {list(result.keys())[:10]}"
    if "tracks" not in result:
        return "issue", f"Response missing tracks: {list(result.keys())[:10]}"

    tracks = result.get("tracks", [])
    transport = result.get("transport", {})

    # Now test detailed mode
    try:
        detailed = conn.send_command("get_session_state", {"detailed": True})
    except Exception as e:
        return "issue", f"Lightweight worked but detailed mode crashed: {e}"

    detailed_tracks = detailed.get("tracks", [])

    # Check that detailed mode has more info (parameters in devices)
    has_params = False
    for t in detailed_tracks:
        for d in t.get("devices", []):
            if "parameters" in d:
                has_params = True
                break
        if has_params:
            break

    return "pass", f"Session state: {len(tracks)} tracks, transport has {list(transport.keys())[:5]}. Detailed mode params: {has_params}"


def reconnect(conn):
    """Reconnect if socket was dropped."""
    try:
        conn.send_command("ping")
        return conn
    except Exception:
        conn.disconnect()
        return connect()


TESTS = [
    ("Browse with Depth", test_browse_with_depth),
    ("Get Session State", test_get_session_state),
    ("Load Instrument by Path", test_load_instrument_by_path),
    ("Get Device Parameters", test_get_device_parameters),
    ("Set Device Parameter by Name", test_set_device_parameter_by_name),
    ("Delete a Device", test_delete_device),
    ("Get Rack Chains", test_get_rack_chains),
    ("Audio Track Load Guard", test_audio_track_load_guard),
]


def main():
    print("Connecting to Ableton...")
    conn = connect()
    print("Connected!\n")

    results = []
    for i, (name, func) in enumerate(TESTS, 1):
        conn = reconnect(conn)
        print(f"--- Test {i}: {name} ---")
        try:
            status, detail = func(conn)
        except Exception as e:
            status, detail = "issue", f"Unhandled exception: {e}"
        results.append((i, name, status, detail))
        icon = {"pass": "PASS", "issue": "ISSUE", "skip": "SKIP"}[status]
        print(f"  [{icon}] {detail}\n")

    conn.disconnect()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for r in results if r[2] == "pass")
    issues = sum(1 for r in results if r[2] == "issue")
    skipped = sum(1 for r in results if r[2] == "skip")
    print(f"  Passed:  {passed}")
    print(f"  Issues:  {issues}")
    print(f"  Skipped: {skipped}")
    print(f"  Total:   {len(results)}")

    # Output JSON for UAT update
    print("\n--- JSON RESULTS ---")
    print(json.dumps(results, indent=2))

    return 0 if issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
