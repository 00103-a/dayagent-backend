from agent_service.agents.tool_selection import ToolSelection, parse_tool_selection


def main():
    output = """是否需要工具：是
工具名称：weather
原因：用户询问实时天气
"""

    selection = parse_tool_selection(output)

    assert isinstance(selection, ToolSelection)
    assert selection.needs_tool is True
    assert selection.tool_name == "weather"
    assert "天气" in selection.reason

    no_tool_output = """是否需要工具：否
工具名称：无
原因：用户只是普通聊天
"""

    no_tool_selection = parse_tool_selection(no_tool_output)

    assert no_tool_selection.needs_tool is False
    assert no_tool_selection.tool_name == ""

    print("tool selection shape ok")


if __name__ == "__main__":
    main()