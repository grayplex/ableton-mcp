"""Browser handlers: browse, search, load instruments and effects."""

import queue
import traceback

from AbletonMCP_Remote_Script.registry import command

# Browser category map -- fixes the 'nstruments' typo by using correct dict keys
_CATEGORY_MAP = {
    "instruments": "instruments",
    "sounds": "sounds",
    "drums": "drums",
    "audio_effects": "audio_effects",
    "midi_effects": "midi_effects",
    "max_for_live": "max_for_live",
    "plug_ins": "plug_ins",
    "clips": "clips",
    "samples": "samples",
    "packs": "packs",
}


class BrowserHandlers:
    """Mixin class for browser command handlers."""

    @command("get_browser_tree")
    def get_browser_tree(self, params=None):
        """Get a simplified tree of browser categories.

        Args:
            params: dict with optional keys:
                - category_type: str (default 'all')
                - max_depth: int (default 1, capped at 5) -- how deep to
                  recurse into children

        Returns:
            Dictionary with the browser tree structure
        """
        category_type = "all"
        max_depth = 1
        if params:
            if isinstance(params, dict):
                category_type = params.get("category_type", "all")
                max_depth = params.get("max_depth", 1)
            elif isinstance(params, str):
                category_type = params
        # Cap max_depth to prevent performance issues
        max_depth = min(max_depth, 5)
        try:
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")

            if not hasattr(app, "browser") or app.browser is None:
                raise RuntimeError("Browser is not available in the Live application")

            browser_attrs = [attr for attr in dir(app.browser) if not attr.startswith("_")]
            self.log_message(f"Available browser attributes: {browser_attrs}")

            result = {
                "type": category_type,
                "max_depth": max_depth,
                "categories": [],
                "available_categories": browser_attrs,
            }

            def process_item(item, depth=0, max_d=1):
                if not item:
                    return None
                info = {
                    "name": item.name if hasattr(item, "name") else "Unknown",
                    "is_folder": hasattr(item, "children") and bool(item.children),
                    "is_device": hasattr(item, "is_device") and item.is_device,
                    "is_loadable": hasattr(item, "is_loadable") and item.is_loadable,
                    "uri": item.uri if hasattr(item, "uri") else None,
                    "children": [],
                }
                if depth < max_d and hasattr(item, "children") and item.children:
                    for child in item.children:
                        child_info = process_item(child, depth + 1, max_d)
                        if child_info:
                            info["children"].append(child_info)
                return info

            if (category_type == "all" or category_type == "instruments") and hasattr(
                app.browser, "instruments"
            ):
                try:
                    instruments = process_item(app.browser.instruments, 0, max_depth)
                    if instruments:
                        instruments["name"] = "Instruments"
                        result["categories"].append(instruments)
                except Exception as e:
                    self.log_message(f"Error processing instruments: {e}")

            if (category_type == "all" or category_type == "sounds") and hasattr(
                app.browser, "sounds"
            ):
                try:
                    sounds = process_item(app.browser.sounds, 0, max_depth)
                    if sounds:
                        sounds["name"] = "Sounds"
                        result["categories"].append(sounds)
                except Exception as e:
                    self.log_message(f"Error processing sounds: {e}")

            if (category_type == "all" or category_type == "drums") and hasattr(
                app.browser, "drums"
            ):
                try:
                    drums = process_item(app.browser.drums, 0, max_depth)
                    if drums:
                        drums["name"] = "Drums"
                        result["categories"].append(drums)
                except Exception as e:
                    self.log_message(f"Error processing drums: {e}")

            if (category_type == "all" or category_type == "audio_effects") and hasattr(
                app.browser, "audio_effects"
            ):
                try:
                    audio_effects = process_item(app.browser.audio_effects, 0, max_depth)
                    if audio_effects:
                        audio_effects["name"] = "Audio Effects"
                        result["categories"].append(audio_effects)
                except Exception as e:
                    self.log_message(f"Error processing audio_effects: {e}")

            if (category_type == "all" or category_type == "midi_effects") and hasattr(
                app.browser, "midi_effects"
            ):
                try:
                    midi_effects = process_item(app.browser.midi_effects, 0, max_depth)
                    if midi_effects:
                        midi_effects["name"] = "MIDI Effects"
                        result["categories"].append(midi_effects)
                except Exception as e:
                    self.log_message(f"Error processing midi_effects: {e}")

            for attr in browser_attrs:
                if attr not in [
                    "instruments",
                    "sounds",
                    "drums",
                    "audio_effects",
                    "midi_effects",
                ] and (category_type == "all" or category_type == attr):
                    try:
                        item = getattr(app.browser, attr)
                        if hasattr(item, "children") or hasattr(item, "name"):
                            category = process_item(item, 0, max_depth)
                            if category:
                                category["name"] = attr.capitalize()
                                result["categories"].append(category)
                    except Exception as e:
                        self.log_message(f"Error processing {attr}: {e}")

            self.log_message(
                f"Browser tree generated for {category_type} "
                f"with {len(result['categories'])} root categories "
                f"(max_depth={max_depth})"
            )
            return result

        except Exception as e:
            self.log_message(f"Error getting browser tree: {e}")
            self.log_message(traceback.format_exc())
            raise

    @command("get_browser_items_at_path")
    def get_browser_items_at_path(self, params):
        """Get browser items at a specific path.

        Args:
            params: dict with 'path' key, or a string path
                   Path format: "category/folder/subfolder"

        Returns:
            Dictionary with items at the specified path
        """
        if isinstance(params, str):
            path = params
        else:
            path = params.get("path", "") if params else ""
        try:
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")

            if not hasattr(app, "browser") or app.browser is None:
                raise RuntimeError("Browser is not available in the Live application")

            browser_attrs = [attr for attr in dir(app.browser) if not attr.startswith("_")]
            self.log_message(f"Available browser attributes: {browser_attrs}")

            path_parts = path.split("/")
            if not path_parts:
                raise ValueError("Invalid path")

            root_category = path_parts[0].lower()
            browser_attr = _CATEGORY_MAP.get(root_category, "")
            current_item = getattr(app.browser, browser_attr, None) if browser_attr else None

            if current_item is None:
                found = False
                for attr in browser_attrs:
                    if attr.lower() == root_category:
                        try:
                            current_item = getattr(app.browser, attr)
                            found = True
                            break
                        except Exception as e:
                            self.log_message(f"Error accessing browser attribute {attr}: {e}")

                if not found:
                    return {
                        "path": path,
                        "error": f"Unknown or unavailable category: {root_category}",
                        "available_categories": browser_attrs,
                        "items": [],
                    }

            for i in range(1, len(path_parts)):
                part = path_parts[i]
                if not part:
                    continue

                if not hasattr(current_item, "children"):
                    return {
                        "path": path,
                        "error": f"Item at '{'/'.join(path_parts[:i])}' has no children",
                        "items": [],
                    }

                found = False
                for child in current_item.children:
                    if hasattr(child, "name") and child.name.lower() == part.lower():
                        current_item = child
                        found = True
                        break

                if not found:
                    return {
                        "path": path,
                        "error": f"Path part '{part}' not found",
                        "items": [],
                    }

            items = []
            if hasattr(current_item, "children"):
                for child in current_item.children:
                    item_info = {
                        "name": child.name if hasattr(child, "name") else "Unknown",
                        "is_folder": hasattr(child, "children") and bool(child.children),
                        "is_device": hasattr(child, "is_device") and child.is_device,
                        "is_loadable": hasattr(child, "is_loadable") and child.is_loadable,
                        "uri": child.uri if hasattr(child, "uri") else None,
                    }
                    items.append(item_info)

            result = {
                "path": path,
                "name": current_item.name if hasattr(current_item, "name") else "Unknown",
                "uri": current_item.uri if hasattr(current_item, "uri") else None,
                "is_folder": hasattr(current_item, "children") and bool(current_item.children),
                "is_device": hasattr(current_item, "is_device") and current_item.is_device,
                "is_loadable": hasattr(current_item, "is_loadable") and current_item.is_loadable,
                "items": items,
            }

            self.log_message(f"Retrieved {len(items)} items at path: {path}")
            return result

        except Exception as e:
            self.log_message(f"Error getting browser items at path: {e}")
            self.log_message(traceback.format_exc())
            raise

    @command("get_browser_item")
    def _get_browser_item(self, params):
        """Get a browser item by URI or path."""
        uri = params.get("uri", None)
        path = params.get("path", None)
        try:
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")

            result = {
                "uri": uri,
                "path": path,
                "found": False,
            }

            if uri:
                item = self._find_browser_item_by_uri(app.browser, uri)
                if item:
                    result["found"] = True
                    result["item"] = {
                        "name": item.name,
                        "is_folder": item.is_folder,
                        "is_device": item.is_device,
                        "is_loadable": item.is_loadable,
                        "uri": item.uri,
                    }
                    return result

            if path:
                path_parts = path.split("/")

                category_name = path_parts[0].lower()
                browser_attr = _CATEGORY_MAP.get(category_name, "")
                current_item = getattr(app.browser, browser_attr, None) if browser_attr else None

                if current_item is None:
                    current_item = app.browser.instruments
                    path_parts = ["instruments"] + path_parts

                for i in range(1, len(path_parts)):
                    part = path_parts[i]
                    if not part:
                        continue

                    found = False
                    for child in current_item.children:
                        if child.name.lower() == part.lower():
                            current_item = child
                            found = True
                            break

                    if not found:
                        result["error"] = f"Path part '{part}' not found"
                        return result

                result["found"] = True
                result["item"] = {
                    "name": current_item.name,
                    "is_folder": current_item.is_folder,
                    "is_device": current_item.is_device,
                    "is_loadable": current_item.is_loadable,
                    "uri": current_item.uri,
                }

            return result
        except Exception as e:
            self.log_message(f"Error getting browser item: {e}")
            self.log_message(traceback.format_exc())
            raise

    @command("get_browser_categories")
    def _get_browser_categories(self, params):
        """Get browser categories.

        Args:
            params: dict with optional 'category_type' key (default 'all')
        """
        category_type = params.get("category_type", "all") if params else "all"
        return self.get_browser_tree({"category_type": category_type})

    @command("get_browser_items")
    def _get_browser_items(self, params):
        """Get browser items at a path.

        Args:
            params: dict with 'path' key and optional 'item_type' key
        """
        path = params.get("path", "") if params else ""
        return self.get_browser_items_at_path({"path": path})

    @command("load_browser_item", write=True, self_scheduling=True)
    def _load_browser_item(self, params):
        """Load a browser item onto a track by URI or path.

        Uses same-callback pattern: selected_track assignment and load_item
        call happen in the same schedule_message callback to prevent the
        race condition where instruments load on the wrong track.

        Includes device count verification and one automatic retry.

        Params:
            track_index: Index of the track to load onto (default 0).
            item_uri: URI of the browser item.
            path: Browser path (e.g. "instruments/Analog"). Used if item_uri
                  is empty/None. Resolved via category map + child navigation.
        """
        track_index = params.get("track_index", 0)
        item_uri = params.get("item_uri", "")
        path = params.get("path", None)

        if track_index < 0 or track_index >= len(self._song.tracks):
            raise IndexError("Track index out of range")

        track = self._song.tracks[track_index]

        app = self.application()

        # --- Path-based resolution (Change 3) ---
        item = None
        if not item_uri and path:
            item = self._resolve_browser_path(app.browser, path)
            if item:
                item_uri = item.uri if hasattr(item, "uri") else ""
                self._browser_path_cache[item_uri] = item
        elif not item_uri and not path:
            raise ValueError("Provide item_uri or path")

        # --- Track-type guard (Change 2) ---
        # Detect if this is an instrument load on an audio track
        is_instrument_category = False
        if path:
            root_part = path.split("/")[0].lower()
            if root_part in ("instruments", "drums"):
                is_instrument_category = True
        elif item_uri:
            # Check if URI belongs to instruments or drums category
            # by inspecting the path cache or URI structure.
            # Ableton URIs use "Synths", "DrumHits" etc. for instrument categories.
            uri_lower = item_uri.lower()
            if any(kw in uri_lower for kw in ("instrument", "drum", "synth")):
                is_instrument_category = True

        if is_instrument_category:
            is_audio_track = (
                hasattr(track, "has_audio_input")
                and track.has_audio_input
                and not track.has_midi_input
            )
            if is_audio_track:
                raise ValueError(
                    "Cannot load instrument on audio track. "
                    "Use a MIDI track instead."
                )

        # Find the browser item by URI (check cache first)
        if item is None and item_uri:
            if item_uri in self._browser_path_cache:
                try:
                    cached = self._browser_path_cache[item_uri]
                    _ = cached.name
                    item = cached
                except (AttributeError, KeyError, RuntimeError):
                    del self._browser_path_cache[item_uri]

            if item is None:
                item = self._find_browser_item_by_uri(app.browser, item_uri)
                if item:
                    self._browser_path_cache[item_uri] = item

        if not item:
            raise ValueError(f"Browser item with URI '{item_uri}' not found")

        response_queue = queue.Queue()
        devices_before = len(track.devices)

        def do_load(retries_remaining=1):
            """Load item on main thread with same-callback pattern."""
            try:
                # CRITICAL: selected_track and load_item in the SAME callback
                self._song.view.selected_track = track
                app.browser.load_item(item)

                self.schedule_message(
                    1,
                    lambda: self._verify_load(
                        track,
                        devices_before,
                        item_uri,
                        item.name,
                        response_queue,
                        retries_remaining,
                    ),
                )
            except Exception as e:
                self.log_message(f"[ERROR] do_load failed: {e}")
                self.log_message(traceback.format_exc())
                response_queue.put({"status": "error", "message": str(e)})

        try:
            self.schedule_message(0, do_load)
        except AssertionError:
            do_load()

        try:
            result = response_queue.get(timeout=30.0)
            if result.get("status") == "error":
                raise Exception(result.get("message", "Unknown load error"))
            return result.get("result", result)
        except queue.Empty:
            return {"loaded": False, "error": "Timeout waiting for instrument load"}

    def _verify_load(
        self, track, devices_before, item_uri, item_name, response_queue, retries_remaining
    ):
        """Verify device count increased after load, retry once if not."""
        try:
            devices_after_count = len(track.devices)
            if devices_after_count > devices_before:
                device_chain = [d.name for d in track.devices]

                # Build parameter list for the newly loaded device (Change 4)
                new_device = track.devices[devices_after_count - 1]
                parameters = []
                try:
                    for i, p in enumerate(new_device.parameters):
                        parameters.append({
                            "index": i,
                            "name": p.name,
                            "value": p.value,
                            "min": p.min,
                            "max": p.max,
                            "is_quantized": p.is_quantized,
                        })
                except Exception as param_err:
                    self.log_message(
                        f"[WARN] Could not read parameters of loaded device: {param_err}"
                    )

                result_dict = {
                    "loaded": True,
                    "item_name": item_name,
                    "track_name": track.name,
                    "uri": item_uri,
                    "devices": device_chain,
                    "device_count": devices_after_count,
                }
                if parameters:
                    result_dict["parameters"] = parameters

                response_queue.put(
                    {
                        "status": "success",
                        "result": result_dict,
                    }
                )
            elif retries_remaining > 0:
                self.log_message(
                    f"[WARN] Load verify failed for {item_uri}, retrying "
                    f"({retries_remaining} retries left)"
                )
                app = self.application()
                item = self._browser_path_cache.get(item_uri)
                if not item:
                    item = self._find_browser_item_by_uri(app.browser, item_uri)

                if item:

                    def retry_load():
                        try:
                            self._song.view.selected_track = track
                            app.browser.load_item(item)
                            self.schedule_message(
                                1,
                                lambda: self._verify_load(
                                    track,
                                    devices_before,
                                    item_uri,
                                    item_name,
                                    response_queue,
                                    retries_remaining - 1,
                                ),
                            )
                        except Exception as e:
                            response_queue.put({"status": "error", "message": str(e)})

                    self.schedule_message(0, retry_load)
                else:
                    response_queue.put(
                        {
                            "status": "error",
                            "message": f"Browser item '{item_uri}' not found on retry",
                        }
                    )
            else:
                device_chain = [d.name for d in track.devices]
                response_queue.put(
                    {
                        "status": "error",
                        "message": (
                            f"Load verification failed for '{item_name}' on track "
                            f"'{track.name}'. Device count unchanged "
                            f"({devices_after_count}). Devices: {device_chain}"
                        ),
                    }
                )
        except Exception as e:
            self.log_message(f"[ERROR] _verify_load: {e}")
            self.log_message(traceback.format_exc())
            response_queue.put({"status": "error", "message": str(e)})

    @command("load_instrument_or_effect", write=True, self_scheduling=True)
    def _load_instrument_or_effect(self, params):
        """Load an instrument or effect by URI. Delegates to _load_browser_item."""
        if "item_uri" not in params and "uri" in params:
            params["item_uri"] = params["uri"]
        return self._load_browser_item(params)

    def _resolve_browser_path(self, browser, path):
        """Resolve a browser path string to a browser item.

        Splits path on "/", maps root to a browser category via _CATEGORY_MAP,
        then navigates children case-insensitively.

        Args:
            browser: The Live browser object.
            path: Path string, e.g. "instruments/Analog".

        Returns:
            The resolved browser item, or None if not found.
        """
        path_parts = path.split("/")
        if not path_parts:
            return None

        root_category = path_parts[0].lower()
        browser_attr = _CATEGORY_MAP.get(root_category, "")
        current_item = getattr(browser, browser_attr, None) if browser_attr else None

        if current_item is None:
            # Try direct attribute lookup
            browser_attrs = [attr for attr in dir(browser) if not attr.startswith("_")]
            for attr in browser_attrs:
                if attr.lower() == root_category:
                    try:
                        current_item = getattr(browser, attr)
                        break
                    except Exception:
                        pass
            if current_item is None:
                return None

        # Navigate remaining path parts
        for i in range(1, len(path_parts)):
            part = path_parts[i]
            if not part:
                continue
            if not hasattr(current_item, "children") or not current_item.children:
                return None
            found = False
            for child in current_item.children:
                if hasattr(child, "name") and child.name.lower() == part.lower():
                    current_item = child
                    found = True
                    break
            if not found:
                return None

        return current_item

    def _find_browser_item_by_uri(self, browser_or_item, uri, max_depth=10, current_depth=0):
        """Find a browser item by its URI."""
        try:
            if hasattr(browser_or_item, "uri") and browser_or_item.uri == uri:
                return browser_or_item

            if current_depth >= max_depth:
                return None

            if hasattr(browser_or_item, "instruments"):
                categories = [
                    browser_or_item.instruments,
                    browser_or_item.sounds,
                    browser_or_item.drums,
                    browser_or_item.audio_effects,
                    browser_or_item.midi_effects,
                ]

                for category in categories:
                    item = self._find_browser_item_by_uri(
                        category, uri, max_depth, current_depth + 1
                    )
                    if item:
                        return item

                return None

            if hasattr(browser_or_item, "children") and browser_or_item.children:
                for child in browser_or_item.children:
                    item = self._find_browser_item_by_uri(child, uri, max_depth, current_depth + 1)
                    if item:
                        return item

            return None
        except Exception as e:
            self.log_message(f"Error finding browser item by URI: {e}")
            return None
