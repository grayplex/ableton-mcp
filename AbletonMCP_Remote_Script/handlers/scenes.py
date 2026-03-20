"""Scene handlers: create, name, fire, delete, color, tempo, time sig, is_empty."""

from AbletonMCP_Remote_Script.handlers.tracks import COLOR_INDEX_TO_NAME, COLOR_NAMES
from AbletonMCP_Remote_Script.registry import command


class SceneHandlers:
    """Mixin class for scene command handlers."""

    @command("create_scene", write=True)
    def _create_scene(self, params):
        """Create a new scene at the given index, optionally naming it."""
        index = params.get("index", -1)
        name = params.get("name", None)
        try:
            scene = self._song.create_scene(index)
            actual_index = (
                len(self._song.scenes) - 1 if index == -1 else index
            )
            if name:
                scene.name = name
            return {
                "index": actual_index,
                "name": scene.name,
            }
        except Exception as e:
            self.log_message(f"Error creating scene: {e}")
            raise

    @command("set_scene_name", write=True)
    def _set_scene_name(self, params):
        """Set the name of a scene by index."""
        scene_index = params.get("scene_index", 0)
        name = params.get("name", "")
        try:
            scenes = self._song.scenes
            if scene_index < 0 or scene_index >= len(scenes):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(scenes) - 1})"
                )
            scenes[scene_index].name = name
            return {"index": scene_index, "name": name}
        except Exception as e:
            self.log_message(f"Error setting scene name: {e}")
            raise

    @command("fire_scene", write=True)
    def _fire_scene(self, params):
        """Fire (launch) all clip slots in a scene."""
        scene_index = params.get("scene_index", 0)
        try:
            scenes = self._song.scenes
            if scene_index < 0 or scene_index >= len(scenes):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(scenes) - 1})"
                )
            scene = scenes[scene_index]
            scene.fire()
            return {
                "fired": True,
                "index": scene_index,
                "name": scene.name,
            }
        except Exception as e:
            self.log_message(f"Error firing scene: {e}")
            raise

    @command("delete_scene", write=True)
    def _delete_scene(self, params):
        """Delete a scene by index. Refuses to delete the last scene."""
        scene_index = params.get("scene_index", 0)
        try:
            scenes = self._song.scenes
            if scene_index < 0 or scene_index >= len(scenes):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(scenes) - 1})"
                )
            if len(scenes) <= 1:
                raise ValueError("Cannot delete the last scene")
            deleted_name = scenes[scene_index].name
            self._song.delete_scene(scene_index)
            return {
                "deleted": True,
                "index": scene_index,
                "name": deleted_name,
            }
        except Exception as e:
            self.log_message(f"Error deleting scene: {e}")
            raise

    @command("duplicate_scene", write=True)
    def _duplicate_scene(self, params):
        """Duplicate a scene by index."""
        scene_index = params.get("scene_index")
        try:
            if scene_index is None:
                raise ValueError("scene_index parameter is required")
            scenes = self._song.scenes
            if scene_index < 0 or scene_index >= len(scenes):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(scenes) - 1})"
                )
            self._song.duplicate_scene(scene_index)
            return {
                "duplicated": True,
                "source_index": scene_index,
                "scene_count": len(self._song.scenes),
            }
        except Exception as e:
            self.log_message(f"Error duplicating scene: {e}")
            raise

    @command("set_scene_color", write=True)
    def _set_scene_color(self, params):
        """Set the color of a scene by friendly name."""
        scene_index = params.get("scene_index", 0)
        color = params.get("color", "")
        try:
            scenes = self._song.scenes
            if scene_index < 0 or scene_index >= len(scenes):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(scenes) - 1})"
                )
            if color not in COLOR_NAMES:
                valid = ", ".join(sorted(COLOR_NAMES.keys()))
                raise ValueError(
                    f"Unknown color '{color}'. Valid colors: {valid}"
                )
            scene = scenes[scene_index]
            scene.color_index = COLOR_NAMES[color]
            return {
                "scene_index": scene_index,
                "name": scene.name,
                "color": color,
            }
        except Exception as e:
            self.log_message(f"Error setting scene color: {e}")
            raise

    @command("get_scene_color")
    def _get_scene_color(self, params):
        """Get the current color of a scene."""
        scene_index = params.get("scene_index", 0)
        try:
            scenes = self._song.scenes
            if scene_index < 0 or scene_index >= len(scenes):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(scenes) - 1})"
                )
            scene = scenes[scene_index]
            color_name = COLOR_INDEX_TO_NAME.get(
                scene.color_index, f"unknown_{scene.color_index}"
            )
            return {
                "scene_index": scene_index,
                "name": scene.name,
                "color": color_name,
                "color_index": scene.color_index,
            }
        except Exception as e:
            self.log_message(f"Error getting scene color: {e}")
            raise

    @command("set_scene_tempo", write=True)
    def _set_scene_tempo(self, params):
        """Set per-scene tempo. Overrides global tempo when fired."""
        scene_index = params.get("scene_index", 0)
        tempo = params.get("tempo", None)
        enabled = params.get("enabled", True)
        try:
            scenes = self._song.scenes
            if scene_index < 0 or scene_index >= len(scenes):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(scenes) - 1})"
                )
            scene = scenes[scene_index]
            if tempo is not None:
                scene.tempo = tempo
            scene.tempo_enabled = enabled
            return {
                "scene_index": scene_index,
                "name": scene.name,
                "tempo": scene.tempo,
                "tempo_enabled": scene.tempo_enabled,
                "note": (
                    "Scene tempo will override global tempo when this "
                    "scene is fired"
                    if scene.tempo_enabled
                    else "Scene tempo disabled, using song tempo"
                ),
            }
        except Exception as e:
            self.log_message(f"Error setting scene tempo: {e}")
            raise

    @command("set_scene_time_signature", write=True)
    def _set_scene_time_signature(self, params):
        """Set per-scene time signature. Overrides global when fired."""
        scene_index = params.get("scene_index", 0)
        numerator = params.get("numerator", None)
        denominator = params.get("denominator", None)
        enabled = params.get("enabled", True)
        try:
            scenes = self._song.scenes
            if scene_index < 0 or scene_index >= len(scenes):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(scenes) - 1})"
                )
            scene = scenes[scene_index]
            if numerator is not None:
                scene.time_signature_numerator = numerator
            if denominator is not None:
                scene.time_signature_denominator = denominator
            scene.time_signature_enabled = enabled
            return {
                "scene_index": scene_index,
                "name": scene.name,
                "numerator": scene.time_signature_numerator,
                "denominator": scene.time_signature_denominator,
                "time_signature_enabled": scene.time_signature_enabled,
                "note": (
                    "Scene time signature will override global when this "
                    "scene is fired"
                    if scene.time_signature_enabled
                    else "Scene time signature disabled, using song "
                    "time signature"
                ),
            }
        except Exception as e:
            self.log_message(f"Error setting scene time signature: {e}")
            raise

    @command("fire_scene_as_selected", write=True)
    def _fire_scene_as_selected(self, params):
        """Fire the selected scene and advance selection to next scene."""
        scene_index = params.get("scene_index", 0)
        force_legato = params.get("force_legato", False)
        try:
            scenes = self._song.scenes
            if scene_index < 0 or scene_index >= len(scenes):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(scenes) - 1})"
                )
            scene = scenes[scene_index]
            self._song.view.selected_scene = scene
            scene.fire_as_selected(force_legato=force_legato)
            return {
                "fired": True,
                "index": scene_index,
                "name": scene.name,
                "force_legato": force_legato,
                "note": "Scene fired and selection advanced to next scene",
            }
        except Exception as e:
            self.log_message(f"Error firing scene as selected: {e}")
            raise

    @command("get_scene_is_empty")
    def _get_scene_is_empty(self, params):
        """Check if a scene has no clips."""
        scene_index = params.get("scene_index", 0)
        try:
            scenes = self._song.scenes
            if scene_index < 0 or scene_index >= len(scenes):
                raise IndexError(
                    f"Scene index {scene_index} out of range "
                    f"(0-{len(scenes) - 1})"
                )
            scene = scenes[scene_index]
            return {
                "scene_index": scene_index,
                "name": scene.name,
                "is_empty": scene.is_empty,
            }
        except Exception as e:
            self.log_message(f"Error checking if scene is empty: {e}")
            raise
