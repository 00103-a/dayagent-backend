# DayAgent — 学习型重构项目

## 当前阶段

项目已由 AI 辅助生成，代码能跑，但我不完全理解。现阶段目标：
**通过重构，把项目代码转化为自己的编程能力和架构思维。**

---

## 学习目标

### 短期（当前在做）
- [ ] 理解并统一 Python 工具层（Tool + ToolResult 契约）
- [ ] 独立完成 API 迁移（快递100 → uapis.cn）→ ✅ 已完成
- [ ] 独立完成新闻模块重写（天行数据 → uapis hotboard）→ 进行中
- [ ] 理解调用链：router → tool → API，数据如何跨层传递

### 中期
- [ ] 掌握 agent 工作流编排（多工具并行调用 + LLM 决策）
- [ ] 理解 Java Spring Boot 基础（拦截器、MyBatis Plus、RestTemplate）
- [ ] 前端 Vue 3 基础（数据流、组件通信）

### 长期
- [ ] 定时任务 + 推送（每日早 8 点规划）
- [ ] ESP32 + MAX98357 语音播报
- [ ] LLM 摘要链（多工具数据 → LLM 口语化 → TTS 语音）

---

## 已掌握 vs 待掌握

| 已掌握 | 待掌握 |
|---|---|
| Python 函数 + 类型注解 | async/await 深层理解 |
| GET 请求 + JSON 解析 | POST + 复杂鉴权 |
| 正则关键词匹配 | 状态机（如学习通模拟登录） |
| 工具契约（Tool/ToolResult） | agent 工作流编排 |
| API 文档阅读 + 迁移 | 从零设计 API |
| httpx 异常处理骨架 | aiohttp / httpx 底层差异 |

---

## 当前项目真实状态

### 工具层统一化进度
- [x] base.py（Tool + ToolResult 契约）
- [x] WeatherTool（AI 写的样板，我读过）
- [x] CourseTool（我自己写的）
- [x] ParcelTool（我亲手改的——API迁移+待取检测+取件码）
- [x] NewsTool（我写的——hotboard 四平台并行拉取）
- [ ] ChaoxingTool（待做）

### 已知但暂时不管的问题
- ParcelStatus 传了 pickup_code 但 Java 端没存
- plan.py 第 48 行语法错误待修：`is_waiting_pickup(...)` 括号应改赋值
- 旧 NEWS_API_KEY / KUAIDI100 环境变量可清理

### 2026-06-16 进展

**Parcel 模块（重点）**
- 快递100 → uapis.cn API 迁移：删 hashlib/STATE_MAP/_build_sign，POST→GET，免费免 Key
- 到站待取关键词检测：_check_waiting_pickup() + _WAITING_PICKUP_PATTERNS 正则匹配
- 签收误判修复：not result["is_delivered"] 条件前置，删 r"已签收" 关键词
- 取件码提取：_extract_pickup_code()，正则 r"取件码[：:为]?\s*([A-Za-z0-9\-]{4,12})"
- carrier 自动回填：空传时从 API 返回的 carrier_name 补上
- ParcelStatus 同步更新：加了 pickup_code、is_waiting_pickup
- plan.py kuaidi100 参数链全部清理

**News 模块（新建重写）**
- 天行数据 API → uapis hotboard API（免费免 Key）
- query_hotboard(type)：拉单个平台热榜，learned extra.abstract 有正文摘要
- get_personalized_news()：asyncio.gather 并行拉 4 平台（weibo/zhihu/baidu/bilibili）
- merge + extend 合并，每平台取前 5 条格式化
- NewsTool 套上 Tool 契约
- goals 参数已占位但未实现关键词筛选

**新学概念**
- async/await 函数拆分规则（有 await 用 async def，没有用 def）
- re.search().group(1) 正则分组提取
- enumerate(items, 1) 自动编号
- asyncio.gather + * 星号拆包 = 并行任务
- extend vs append 列表合并
- str() 类型强转的作用
- resp.json() 为何也要 try/except
- router → tool → API 调用链完整理解

---

## 工作方式（非常重要）

### 必须遵守
- **代码我来写**：你提供代码片段和讲解，我自己敲进文件。不要直接编辑我的代码。
- **一步步来**：分小段给我，一段敲完再下一段
- **不懂就问**：允许我随时打断，解释概念和原理
- **我是新手**：Python 和 Java 基础都不牢固，讲概念用类比

### 会话约定
- **开始吧**：先读 CLAUDE.md 获取最新进展，接上上次进度
- **今天就到这里了**：更新 CLAUDE.md 记录当天进展，并在终端给出本次会话的总结（做了什么、学了什么、接下来做什么）

### 不需要的
- 一次性写完整个文件
- 跳过基础概念的解释
- 替我操作 git / 环境配置（除非我明确请求）

---

## 项目架构概要（仅作参考）

```
前端 Vue3 + Electron → Java Spring Boot → Python FastAPI
                                              ├── routers/（接口层）
                                              ├── tools/（工具层，正在重构）
                                              ├── agents/（LLM 调用）
                                              └── schemas/（数据模型）
```

---

## 远期想法

- 每日定时闹铃：ESP32 + MAX98357 语音播报
- LLM 口语化摘要：多工具数据 → 一段 200 字播报
- 晚间打卡引导：基于早上 plan 反向填充总结模板
