"""Tests verifying Python 2 compatibility code removal and Python 3.11 idiom adoption.

These tests grep the actual source files to confirm:
- No Python 2 compatibility code remains
- Python 3.11 idioms are used consistently
- No bare except blocks exist
"""

import re


def test_no_future_imports(remote_script_source):
    """Verify no 'from __future__' imports remain in the Remote Script."""
    assert "from __future__" not in remote_script_source, (
        "Found 'from __future__' import -- Python 2 compatibility code should be removed"
    )


def test_no_queue_compat_hack(remote_script_source):
    """Verify the Python 2 Queue import hack is removed and direct import queue is used."""
    # Should NOT have the old Python 2 Queue import
    assert "import Queue" not in remote_script_source, (
        "Found 'import Queue' -- Python 2 Queue compatibility hack should be removed"
    )
    # SHOULD have the direct Python 3 import
    assert "import queue" in remote_script_source, (
        "Missing 'import queue' -- direct Python 3 queue import should be present"
    )


def test_no_attribute_error_decode_branches(remote_script_source):
    """Verify no try/except AttributeError blocks for encode/decode remain."""
    # Look for except AttributeError blocks that are part of Python 2 compat patterns
    # These blocks have comments like "Python 2" near them
    lines = remote_script_source.splitlines()
    for i, line in enumerate(lines):
        if "except AttributeError" in line:
            # Check surrounding context (2 lines before and after) for Python 2 comments
            context_start = max(0, i - 2)
            context_end = min(len(lines), i + 3)
            context = "\n".join(lines[context_start:context_end])
            if "Python 2" in context or "decode" in context or "encode" in context:
                assert False, (
                    f"Found Python 2 encode/decode compatibility block at line {i + 1}:\n{context}"
                )


def test_super_calls_used(remote_script_source):
    """Verify old-style super calls are replaced with Python 3 super()."""
    assert "ControlSurface.__init__" not in remote_script_source, (
        "Found old-style 'ControlSurface.__init__' -- should use super().__init__()"
    )
    assert "ControlSurface.disconnect(self)" not in remote_script_source, (
        "Found old-style 'ControlSurface.disconnect(self)' -- should use super().disconnect()"
    )
    assert "super().__init__" in remote_script_source, (
        "Missing 'super().__init__' -- Python 3 super() should be used for __init__"
    )
    assert "super().disconnect()" in remote_script_source, (
        "Missing 'super().disconnect()' -- Python 3 super() should be used for disconnect"
    )


def test_no_bare_excepts(remote_script_source, server_source):
    """Verify no bare 'except:' blocks exist in either source file."""
    bare_except_pattern = re.compile(r"except\s*:")

    remote_matches = bare_except_pattern.findall(remote_script_source)
    assert len(remote_matches) == 0, (
        f"Found {len(remote_matches)} bare 'except:' block(s) in Remote Script -- "
        "all exception handlers must catch a specific type"
    )

    server_matches = bare_except_pattern.findall(server_source)
    assert len(server_matches) == 0, (
        f"Found {len(server_matches)} bare 'except:' block(s) in MCP server -- "
        "all exception handlers must catch a specific type"
    )


def test_f_strings_used(remote_script_source):
    """Verify f-strings are used and .format() calls are minimal."""
    format_count = remote_script_source.count('".format(')
    format_count += remote_script_source.count("'.format(")
    assert format_count <= 2, (
        f"Found {format_count} .format() calls -- should use f-strings instead (max 2 allowed)"
    )

    f_string_count = remote_script_source.count('f"') + remote_script_source.count("f'")
    assert f_string_count > 10, (
        f"Found only {f_string_count} f-string usages -- should use f-strings throughout (expected >10)"
    )
