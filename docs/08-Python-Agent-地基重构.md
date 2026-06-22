# 08 - Python Agent 地基重构

## 1. 这阶段的目标

这一阶段不是为了马上做一个“会自主思考的完整 Agent”，而是先把 DayAgent 的 Python 后端从“函数堆在一起直接调用”，整理成可以继续演化的 Agent 地基。

一句话：

> 先让所有工具说同一种话，再让上层 workflow 用统一方式组织它们。

原来的问题是：

- 天气、课表、快递、学习通、新闻各自有自己的函数名和参数形式。
- `plan.py` 直接知道太多细节，比如天气怎么查、课表怎么拿、快递怎么整理。
- 后面如果想让 AI 自己选择工具，会发现工具没有统一入口。

这一阶段的重构方向是：

```text
散落函数
  ↓
Tool 统一接口
  ↓
registry 工具注册表
  ↓
workflow 编排层
  ↓
tool prompt
  ↓
tool selection 结构化结果
```

这就是从“业务代码写死调用”走向“Agent + 工作流编排”的第一步。

## 2. 当前完成的结构

### 2.1 Tool / ToolResult

文件：

```text
agent_service/tools/base.py
```

这里定义了两个核心东西：

- `Tool`
- `ToolResult`

`Tool` 是所有工具的统一父类。每个工具都要有：

```python
name: str
description: str
async def run(self, params: dict) -> ToolResult
```

这代表所有工具都遵守同一个约定：

```python
result = await tool.run(params)
```

以前上层要记住：

```python
fetch_weather(...)
get_today_courses(...)
query_parcels(...)
```

现在上层只需要知道：

```python
tool = get_tool("weather")
result = await tool.run({...})
```

`ToolResult` 是统一返回格式：

```python
ToolResult(
    ok=True,
    data={...},
    error="",
)
```

这样上层不用猜每个工具是返回字符串、字典还是列表。它只看：

- `ok`：工具成功没有
- `data`：真正的数据
- `error`：失败原因

### 2.2 工具注册表

文件：

```text
agent_service/tools/registry.py
```

它的作用是做一个“工具箱目录”。

现在工具统一注册在：

```python
TOOLS: dict[str, Tool] = {
    WeatherTool.name: WeatherTool(),
    CourseTool.name: CourseTool(),
    ParcelTool.name: ParcelTool(),
    NewsTool.name: NewsTool(),
    ChaoxingTool.name: ChaoxingTool(),
}
```

上层通过：

```python
get_tool("weather")
```

拿到工具对象。

它还提供：

```python
list_tools()
get_tool_descriptions()
format_tool_descriptions()
```

这几个函数是给后面的 Agent 用的。因为 AI 需要知道“有哪些工具、每个工具能干什么”，所以工具的 `name + description` 不能只给代码看，也要能整理成 prompt 文本给 LLM 看。

### 2.3 Planning Workflow

文件：

```text
agent_service/workflows/planning.py
```

这是阶段 A 最重要的结构变化。

以前 `routers/plan.py` 里面会直接做很多事：

- 查天气
- 查学习通
- 查课表
- 查快递
- 查长期记忆
- 调用 `generate_plan()`
- 组装返回值

现在这些编排逻辑被挪到了 workflow 层。

核心函数是：

```python
async def run_planning_workflow(req: PlanRequest) -> PlanResponse:
```

它代表“完整跑一遍今日规划流程”。

内部大概是：

```text
PlanRequest req
  ↓
collect_tool_context(req)
  ↓
collect_memory_context(req)
  ↓
collect_planning_context(req)
  ↓
generate_plan(...)
  ↓
PlanResponse
```

这样 `plan.py` 就可以变薄。路由层只负责 HTTP 入口和简单校验，真正业务流程交给 workflow。

### 2.4 ToolContext / PlanningContext

文件：

```text
agent_service/workflows/planning.py
```

这里用了两个 `@dataclass`：

```python
@dataclass
class ToolContext:
    weather_info: dict
    course_info: str
    chaoxing_tasks: str
    parcels_summary: str
    parcel_statuses: list[ParcelStatus]
```

```python
@dataclass
class PlanningContext:
    weather_info: dict
    course_info: str
    chaoxing_tasks: str
    parcels_summary: str
    parcel_statuses: list[ParcelStatus]
    memory_hint: str
```

它们的意义是：把多个来源的数据整理成一个有名字的结构，而不是到处传一堆零散变量。

`ToolContext` 只表示工具层拿到的数据。

`PlanningContext` 表示生成规划需要的完整上下文，多了一个长期记忆 `memory_hint`。

这是 workflow 思维的关键：

> 每一步输入什么、输出什么，要有清楚的结构。

### 2.5 Tool Prompt

文件：

```text
agent_service/prompts/agent_tool_prompt.txt
agent_service/agents/tool_prompt.py
```

`agent_tool_prompt.txt` 是给 LLM 的工具选择说明。

`tool_prompt.py` 负责把注册表里的工具描述填进去：

```python
def build_tool_prompt() -> str:
    template = _PROMPT_PATH.read_text(encoding="utf-8")
    tools = format_tool_descriptions()
    return template.replace("{tools}", tools)
```

这一步的意义是：

> 工具列表不再硬编码在 prompt 里，而是从 registry 自动生成。

以后你新增一个工具，只要注册到 `TOOLS`，它就能自动出现在工具 prompt 里。

### 2.6 Tool Selection

文件：

```text
agent_service/agents/tool_selection.py
```

这一步还没有真正让 LLM 调工具，只是先定义“AI 选工具的结果长什么样”。

目标是把类似这样的文本：

```text
是否需要工具：是
工具名称：weather
原因：用户询问实时天气
```

解析成 Python 能处理的对象：

```python
ToolSelection(
    needs_tool=True,
    tool_name="weather",
    reason="用户询问实时天气",
)
```

这一步非常重要，因为 LLM 输出的是自然语言，而代码需要结构化数据。

阶段 A 先做解析结构，不急着接真实 LLM，是为了让地基更稳。

## 3. 今日规划现在怎么流转

现在 `/generate-plan` 的大致链路是：

```text
Java 调 Python /generate-plan
  ↓
agent_service/routers/plan.py
  ↓
run_planning_workflow(req)
  ↓
collect_planning_context(req)
  ↓
并行收集：
  - weather tool
  - course tool
  - chaoxing tool
  - parcel tool
  - memory analysis
  ↓
generate_plan(...)
  ↓
PlanResponse
  ↓
Java
```

这里最核心的变化是：

```text
plan.py 不再直接认识 fetch_weather()
plan.py 只认识 run_planning_workflow(req)
workflow 不直接 import 每个旧函数
workflow 通过 get_tool("weather") 拿工具
```

这说明项目已经开始从“写死调用”转向“可编排流程”。

## 4. 为什么这是 Agent 的地基

真正的 Agent 一般需要三件事：

```text
1. 知道有哪些工具
2. 能判断什么时候用哪个工具
3. 能调用工具并根据结果继续回答
```

阶段 A 已经完成前两件事的基础：

- `registry.py` 让系统知道有哪些工具。
- `format_tool_descriptions()` 让 LLM 也能知道有哪些工具。
- `agent_tool_prompt.txt` 告诉 LLM 怎么判断是否需要工具。
- `ToolSelection` 让代码能读懂 LLM 的选择结果。

下一步才会进入：

```text
LLM 判断工具
  ↓
parse_tool_selection()
  ↓
get_tool(selection.tool_name)
  ↓
tool.run(params)
  ↓
把结果交给 LLM 继续生成回答
```

这就是从 workflow 走向真正 agent 化的路径。

## 5. 测试方式

阶段 A 当前使用轻量 shape tests，不是完整业务集成测试。

统一命令：

```bash
python -m agent_service.tests.run_shape_tests
```

成功时应看到：

```text
tool registry shape ok
tool prompt shape ok
tool selection shape ok
planning workflow shape ok
all shape tests ok
```

本地可能还会看到：

```text
[weather] api_key is EMPTY
[Plan] 长期记忆分析降级: ...
```

这两个不一定是错误。

- `weather api_key is EMPTY`：说明测试环境没配置天气 key。
- `长期记忆分析降级`：说明本地 MySQL 没连上，workflow 走了降级逻辑。

只要最后出现 `all shape tests ok`，就说明阶段 A 的结构没有断。

## 6. 当前阶段结论

阶段 A 已经基本完成：

- 工具统一接口已经有了。
- 工具注册表已经有了。
- 规划 workflow 已经从路由层拆出来。
- 工具 prompt 已经能从 registry 自动生成。
- 工具选择结果已经有了解析结构。
- shape tests 已经覆盖这几个关键结构。

现在 DayAgent 的 Python agent-service 不再只是“能跑的一堆函数”，而是已经有了 Agent 化的基础骨架。

## 7. 下一阶段

下一阶段进入 Phase B：

```text
回看 Java 调 Python 链路
```

要重点理解这些文件：

```text
business-service/src/main/java/com/dayagent/controller/PlanController.java
business-service/src/main/java/com/dayagent/service/AgentCallerService.java
business-service/src/main/java/com/dayagent/service/AgentHttpClient.java
business-service/src/main/java/com/dayagent/service/PlanRequest.java
business-service/src/main/java/com/dayagent/service/PlanResponse.java
```

Phase B 的目标不是立刻大改 Java，而是把这条链路弄懂：

```text
前端点击刷新规划
  ↓
Java /api/plan
  ↓
Java 组装 PlanRequest
  ↓
Java 调 Python /generate-plan
  ↓
Python workflow 生成 PlanResponse
  ↓
Java 缓存 / 持久化 / 返回前端
```

等这条链路理解清楚，再决定 Java 哪些地方需要模块化。

