# 09 - AI 对话 Agent 模块

## 这次改动的目标

这次不是做一个“调用大模型的聊天框”，而是把 AI 对话升级成一个更接近 Agent 的模块：它需要先分析用户需求，再结合用户的个人情况回答。

核心变化：

```text
用户输入
  -> Java 鉴权并收集可信个人上下文
  -> Python Chat Workflow 分析需求
  -> 可选调用工具
  -> 生成带依据的个性化回复
```

## 模块职责

### 前端

新增：

- `frontend/src/api/chat.js`
- `frontend/src/views/ChatView.vue`
- `frontend/src/components/home/ChatInline.vue`

职责：

- 只负责发送用户输入和展示回复。
- 展示 `need_analysis`、`used_context`、`tool_results`，方便观察 Agent 是否真的参考了用户情况。
- 不在前端拼完整个人上下文，因为前端数据可以缺失，也不应该被完全信任。

### Java 业务层

新增：

- `ChatController.java`
- `ChatService.java`

修改：

- `AgentHttpClient.java` 增加 `callChat()`
- `LifeController.java` 移除旧 `/api/chat`

职责：

- `ChatController`：只处理 `/api/chat` 和登录用户识别。
- `ChatService`：从数据库收集可信上下文，包括今日规划、活跃目标、最近总结、未签收快递、默认城市。
- `AgentHttpClient`：统一负责 Java -> Python HTTP 调用。

为什么不继续放在 `LifeController`？

AI 对话不是生活模块代理。它会横跨规划、目标、总结、快递、课程、长期记忆。单独拆出 `ChatController + ChatService` 后，后续做总结反馈、晚间复盘、长期记忆闭环会更自然。

### Python Agent 层

新增：

- `agent_service/workflows/chat.py`
- `agent_service/tests/test_chat_workflow_shape.py`

修改：

- `agent_service/routers/chat.py` 变薄，只调用 workflow。
- `agent_service/tests/run_shape_tests.py` 纳入 chat workflow shape test。

职责：

- `run_chat_workflow()` 是 Agent Chat 的主流程。
- `analyze_need()` 先让 LLM 判断用户真实需求。
- `build_personal_context_text()` 把 Java 传来的结构化上下文整理成 prompt 文本。
- `collect_tool_results()` 根据需求选择性调用 weather/course/chaoxing/parcel/news 工具。
- 最终回复要求说明参考依据，并给出具体下一步。

## 为什么这样更接近 Agent

普通聊天：

```text
用户消息 -> LLM -> 回复
```

现在的 Agent Chat：

```text
用户消息
  -> 需求分析
  -> 个人上下文整理
  -> 工具选择
  -> 工具执行
  -> 基于上下文和工具结果回复
```

它至少具备了三种 Agent 特征：

1. 会判断需求类型，而不是直接回答。
2. 会使用个人上下文，而不是只看当前一句话。
3. 会选择工具，而不是所有问题都只靠模型记忆。

## 当前限制

- 工具选择还是单轮选择，不是多步循环。
- 聊天历史目前只保存在前端页面状态，没有入库。
- Python 的需求分析依赖 LLM；LLM 失败时会走关键词兜底。
- 学习通工具当前仍是降级状态，所以作业相关回答还不能完全准确。

## 下一步优化方向

1. 增加 chat history 表，把独立 Chat 页历史持久化。
2. 把需求分析输出升级成更稳定的 Pydantic schema。
3. 支持多步工具循环：分析 -> 工具 -> 再分析 -> 追问或回答。
4. 总结页提交后复用 `run_chat_workflow()` 做 AI 情绪反馈。
5. 把 `used_context` 和 `tool_results` 做成调试面板，正常用户模式下可折叠。

## 验证

已通过：

```bash
python -m agent_service.tests.run_shape_tests
mvn test
npm run build
```

说明：Python shape test 中长期记忆会尝试连接 MySQL，当前本地没有 root 免密连接，所以会打印降级日志，但测试本身通过。
