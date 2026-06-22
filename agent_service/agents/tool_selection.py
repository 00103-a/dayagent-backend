import re
from dataclasses import dataclass


@dataclass
class ToolSelection:
    needs_tool: bool
    tool_name: str = ""
    reason: str = ""


def _read_field(text: str, label: str) -> str:
    match = re.search(rf"{label}\s*[:：]\s*(.+)", text)
    if not match:
        return ""
    return match.group(1).strip()


def parse_tool_selection(text: str) -> ToolSelection:
    needs_tool_text = _read_field(text, "是否需要工具")
    tool_name = _read_field(text, "工具名称")
    reason = _read_field(text, "原因")

    needs_tool = needs_tool_text.startswith("是")

    if not needs_tool or tool_name == "无":
        tool_name = ""

    return ToolSelection(
        needs_tool=needs_tool,
        tool_name=tool_name,
        reason=reason,
    )