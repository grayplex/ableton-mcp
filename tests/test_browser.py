"""Smoke tests for browser domain tools."""



async def test_browser_tools_registered(mcp_server):
    """Browser tools are registered as MCP tools."""
    tools = await mcp_server.list_tools()
    names = {t.name for t in tools}
    assert "get_browser_tree" in names
    assert "get_browser_items_at_path" in names
    assert "load_drum_kit" in names


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
    text = result[0].text
    assert "Instruments" in text
    assert "Drums" in text
