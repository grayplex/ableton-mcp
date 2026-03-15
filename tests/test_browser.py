"""Smoke tests for browser domain tools."""

import json


async def test_browser_tools_registered(mcp_server):
    """Browser tools are registered; load_drum_kit is NOT registered."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_browser_tree" in names
    assert "get_browser_items_at_path" in names
    assert "load_drum_kit" not in names


async def test_get_browser_tree_returns_data(mcp_server, mock_connection):
    """get_browser_tree returns formatted tree output from mocked response."""
    mock_connection.send_command.return_value = {
        "total_folders": 3,
        "categories": [
            {"name": "Instruments", "path": "instruments", "children": []},
            {"name": "Drums", "path": "drums", "children": []},
        ],
    }
    result = await mcp_server.call_tool("get_browser_tree", {"category_type": "all"})
    text = result[0][0].text
    assert "Instruments" in text
    assert "Drums" in text


async def test_get_browser_tree_max_depth(mcp_server, mock_connection):
    """get_browser_tree passes max_depth to send_command."""
    mock_connection.send_command.return_value = {
        "total_folders": 5,
        "categories": [
            {"name": "Instruments", "path": "instruments", "children": []},
        ],
    }
    result = await mcp_server.call_tool(
        "get_browser_tree", {"category_type": "all", "max_depth": 2}
    )
    call_args = mock_connection.send_command.call_args
    params = call_args[0][1]
    assert params["max_depth"] == 2


async def test_get_browser_items_at_path(mcp_server, mock_connection):
    """get_browser_items_at_path returns JSON response."""
    mock_connection.send_command.return_value = {
        "path": "instruments/Analog",
        "items": [{"name": "Analog", "is_loadable": True}],
    }
    result = await mcp_server.call_tool(
        "get_browser_items_at_path", {"path": "instruments/Analog"}
    )
    text = result[0][0].text
    data = json.loads(text)
    assert data["path"] == "instruments/Analog"
    assert data["items"][0]["is_loadable"] is True
