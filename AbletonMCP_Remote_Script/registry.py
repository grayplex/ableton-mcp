"""Command registry with decorator-based handler registration.

Usage in handler modules::

    from AbletonMCP_Remote_Script.registry import command

    class MyHandlers:
        @command("my_read_cmd")
        def _my_read_cmd(self, params=None):
            ...

        @command("my_write_cmd", write=True)
        def _my_write_cmd(self, params):
            ...

        @command("my_scheduled_cmd", write=True, self_scheduling=True)
        def _my_scheduled_cmd(self, params):
            ...
"""


class CommandRegistry:
    """Collects @command-decorated handlers and builds dispatch tables.

    Decorators record (cmd_name, method_name, is_write, is_self_scheduling)
    tuples at import time. AbletonMCP.__init__ calls build_tables(self)
    to bind handlers to the instance and produce dispatch dicts.
    """

    _entries: list[tuple[str, str, bool, bool]] = []

    @classmethod
    def command(cls, name: str, *, write: bool = False, self_scheduling: bool = False):
        """Register a command handler.

        Args:
            name: Wire command name (e.g., 'get_session_info')
            write: If True, dispatched on Ableton's main thread
            self_scheduling: If True, handler manages its own schedule_message calls
        """
        def decorator(func):
            cls._entries.append((name, func.__name__, write, self_scheduling))
            return func
        return decorator

    @classmethod
    def build_tables(cls, instance):
        """Bind registered handlers to instance and return dispatch dicts.

        Returns:
            (read_commands, write_commands, self_scheduling_commands)
            where self_scheduling_commands is a set of command names.
        """
        read_commands = {}
        write_commands = {}
        self_scheduling = set()
        for cmd_name, method_name, is_write, is_self_sched in cls._entries:
            handler = getattr(instance, method_name)
            if is_write:
                write_commands[cmd_name] = handler
                if is_self_sched:
                    self_scheduling.add(cmd_name)
            else:
                read_commands[cmd_name] = handler
        return read_commands, write_commands, self_scheduling


# Convenience alias for use in handler modules
command = CommandRegistry.command
