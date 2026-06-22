from pathlib import Path

from agent_service.tools.registry import format_tool_descriptions


_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "agent_tool_prompt.txt"


def build_tool_prompt() -> str:
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    tools = format_tool_descriptions()
    return template.replace("{tools}", tools)