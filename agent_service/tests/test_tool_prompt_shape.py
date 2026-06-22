from agent_service.agents.tool_prompt import build_tool_prompt


def main():
    prompt = build_tool_prompt()

    assert isinstance(prompt, str)
    assert "{tools}" not in prompt
    assert "weather" in prompt
    assert "course" in prompt
    assert "parcel" in prompt
    assert "是否需要工具" in prompt
    assert "工具名称" in prompt

    print("tool prompt shape ok")


if __name__ == "__main__":
    main()