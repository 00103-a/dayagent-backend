import asyncio

from agent_service.tests.test_planning_workflow_shape import main as run_planning_shape
from agent_service.tests.test_tool_registry_shape import main as run_registry_shape
from agent_service.tests.test_tool_prompt_shape import main as run_tool_prompt_shape
from agent_service.tests.test_tool_selection_shape import main as run_tool_selection_shape
from agent_service.tests.test_chat_workflow_shape import main as run_chat_workflow_shape
def main():
    run_registry_shape()
    run_tool_prompt_shape()
    run_tool_selection_shape()
    run_chat_workflow_shape()
    asyncio.run(run_planning_shape())
    print("all shape tests ok")


if __name__ == "__main__":
    main()