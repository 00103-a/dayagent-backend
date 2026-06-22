from agent_service.tools.base import Tool
from agent_service.tools.registry import (
    format_tool_descriptions,
    get_tool,
    get_tool_descriptions,
    list_tools,
)

def main():
    expected_tools = {
        "weather",
        "course",
        "parcel",
        "news",
        "chaoxing",
    }

    tool_names = set(list_tools())

    assert expected_tools.issubset(tool_names)

    for name in expected_tools:
        tool = get_tool(name)

        assert isinstance(tool, Tool)
        assert tool.name == name
        assert isinstance(tool.description, str)
        assert tool.description
        assert callable(tool.run)

    descriptions = get_tool_descriptions()

    assert isinstance(descriptions, list)

    for item in descriptions:
        assert isinstance(item, dict)
        assert isinstance(item.get("name"), str)
        assert isinstance(item.get("description"), str)
        assert item["name"]
        assert item["description"]

    tools_text = format_tool_descriptions()

    assert isinstance(tools_text, str)
    assert "weather" in tools_text
    assert "course" in tools_text
    assert "parcel" in tools_text

    print("tool registry shape ok")

    


if __name__ == "__main__":
    main()