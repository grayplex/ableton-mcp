"""Handler modules for AbletonMCP Remote Script.

Importing this package triggers @command decorator registration
for all handler modules. Each module defines a mixin class whose
methods become part of the AbletonMCP class via multiple inheritance.

NOTE: If relative imports fail in Ableton's Python runtime, switch to
absolute imports: from AbletonMCP_Remote_Script.handlers import base, ...
"""

from . import automation, base, browser, clips, devices, mixer, notes, scenes, tracks, transport  # noqa: F401
