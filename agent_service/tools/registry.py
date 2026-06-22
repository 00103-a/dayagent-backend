from agent_service.tools.base import Tool
from agent_service.tools.weather import WeatherTool
from agent_service.tools.courses import CourseTool
from agent_service.tools.parcel import ParcelTool
from agent_service.tools.news import NewsTool
from agent_service.tools.chaoxing import ChaoxingTool

TOOLS: dict[str, Tool] = {
    WeatherTool.name: WeatherTool(),
    CourseTool.name: CourseTool(),
    ParcelTool.name: ParcelTool(),
    NewsTool.name: NewsTool(),
    ChaoxingTool.name: ChaoxingTool(),
}

def get_tool(name: str) -> Tool:
    return TOOLS[name]

def list_tools() -> list[str]:
    return list(TOOLS.keys())

def get_tool_descriptions() -> list[dict[str, str]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
        }
        for tool in TOOLS.values()
    ]
def format_tool_descriptions() -> str:
    return "\n".join(
        f"- {item['name']}: {item['description']}"
        for item in get_tool_descriptions()
    )