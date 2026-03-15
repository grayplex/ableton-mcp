"""Scene handlers: create, name, fire, delete."""

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
