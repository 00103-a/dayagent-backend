# Agent Service 结构测试说明

这些测试是轻量级的重构护栏。

它们不验证真实天气、MySQL 数据、快递接口或 LLM 输出。
它们只验证：重构之后，内部结构的“形状”还对不对。

## 运行方式

在项目根目录运行：

```powershell
python -m agent_service.tests.run_shape_tests
```

预期最后看到：

```text
tool registry shape ok
planning workflow shape ok
all shape tests ok
```

## 保护什么

### `test_tool_registry_shape.py`

保护工具注册表：

- 核心工具已经注册：`weather`、`course`、`parcel`、`news`、`chaoxing`
- 每个工具都是 `Tool`
- 每个工具都有 `name`
- 每个工具都有 `description`
- 每个工具都有可调用的 `run()`
- `get_tool_descriptions()` 返回的结构适合以后喂给 agent

### `test_planning_workflow_shape.py`

保护规划工作流：

- `collect_tool_context()` 返回 `ToolContext`
- `collect_planning_context()` 返回 `PlanningContext`
- workflow 上下文字段的基础类型没有乱

例如：

- `weather_info` 是 `dict`
- `course_info` 是 `str`
- `chaoxing_tasks` 是 `str`
- `parcels_summary` 是 `str`
- `parcel_statuses` 是 `list`
- `memory_hint` 是 `str`

## 正常日志

本地没有完整配置时，看到这些日志是正常的：

```text
[weather] api_key is EMPTY
[Plan] 长期记忆分析降级: ...
```

含义是：外部依赖没有配置完整，但降级路径正常工作。

这些不是测试失败。
