# DayAgent - 个人每日智能规划助手

## 项目定位

用户每天早上一键获取当日行动建议。Agent 融合天气、学习通作业、教务课表、昨日总结、目标计划、个性化新闻、快递状态等多源数据，生成个性化日程规划，晚上记录总结形成闭环。

**核心价值**：不是简单提醒，而是结合用户历史行为规律做智能决策，平台自己做不到这一点。

---

## 架构概览

```
Vue 3 + Electron 桌面端
    ↓ HTTP (JWT Bearer token)
Java Spring Boot（业务层）
    - 用户管理 / JWT 鉴权（拦截器方式）
    - 定时任务（每日早推送，待实现）
    - 数据持久化（MySQL）
    - 目标管理 / 总结存储
    - 快递单号管理
    - 生活模块代理（天气/新闻/课表/学习通 → Python）
    ↓ HTTP 内部调用
Python FastAPI（Agent 层）
    - 学习通数据抓取
    - 教务系统课表抓取（Playwright 浏览器自动化）
    - 天气 API 调用（和风天气，返回 condition_text + condition_icon）
    - 新闻拉取 + LLM 个性化筛选
    - 快递状态查询（快递100 API）
    - DeepSeek LLM 调用
    - 长期记忆分析（精力趋势 + 规划总结对比 + 目标进度检查）
    - 规划生成
```

---

## 技术栈

| 层 | 技术 |
|---|---|
| 移动端 | React Native (Expo SDK 54) — 代码在 E:\dayagent-mobile |
| 前端 | Vue 3 + Vite + Electron（桌面端已接入） |
| 业务后端 | Java 17 + Spring Boot 3.4 + MyBatis Plus 3.5 + jjwt 0.12 |
| Agent 后端 | Python 3.11 + FastAPI + Playwright + httpx |
| LLM | DeepSeek（OpenAI 兼容接口，通过 openai 包调用） |
| 关系型数据库 | MySQL 8（aiomysql 连接池用于 Python 端只读查询） |
| 缓存 | 前端 sessionStorage 按日期分桶缓存（当天有效） |
| 向量数据库 | 待定（第三阶段再选，Chroma/Milvus 均可） |
| 推送 | 企业微信机器人 Webhook（stub，仅打印到控制台） |

---

## 模块划分

### Java 端（business-service）

```
src/main/java/com/dayagent/
├── DayAgentApplication.java
├── common/
│   ├── Result.java                 # 统一响应包装器 {code, message, data}
│   └── BusinessException.java
├── controller/
│   ├── UserController.java
│   ├── GoalController.java
│   ├── SummaryController.java
│   ├── PlanController.java         # GET /api/plan（缓存优先，支持 forceRefresh）
│   ├── ParcelController.java
│   ├── LifeController.java         # 生活模块聚合代理，透传 condition_text/condition_icon
│   └── ChatController.java         # AI 对话接口（注入用户上下文 → DeepSeek）
├── service/
│   ├── AgentCallerService.java
│   ├── AgentHttpClient.java
│   ├── LifeAgentClient.java        # callWeather() 返回 Map{weather, condition_text, condition_icon}
│   ├── ChatService.java            # 拼装上下文 system prompt → 调 Python /chat
│   ├── PlanRequest.java / PlanResponse.java
│   ├── PushService.java
│   └── ScheduleService.java
├── entity/
│   ├── User.java / DailySummary.java / Goal.java
│   ├── DailyPlan.java / Parcel.java
├── mapper/
│   ├── UserMapper.java / GoalMapper.java / DailySummaryMapper.java
│   ├── DailyPlanMapper.java / ParcelMapper.java
├── config/
│   ├── SecurityConfig.java / JwtUtils.java
│   ├── WebConfig.java / RestTemplateConfig.java
├── interceptor/
│   └── JwtInterceptor.java
├── context/
│   └── UserContext.java
└── handler/
    └── GlobalExceptionHandler.java
```

### Python 端（agent-service）

```
agent_service/
├── main.py
├── routers/
│   ├── plan.py / courses.py / weather.py
│   ├── news.py / chaoxing.py
│   └── chat.py                     # POST /chat（AI 对话，带用户上下文）
├── agents/
│   ├── planner.py
│   └── memory.py
├── tools/
│   ├── weather.py                  # fetch_weather() 返回 dict{weather, condition_text, condition_icon}
│   ├── chaoxing.py / jwc.py
│   ├── courses.py / news.py / parcel.py
│   ├── music.py                    # 网易云音乐（每日推荐 + 喜欢列表 + 播放链接）
│   └── mysql_client.py
├── schemas/
│   └── plan_request.py
├── prompts/
│   └── planner_prompt.txt          # priorities 要求 4~5 条，每条 ≤30 字
└── data/
    └── courses.json
```

### 前端（frontend）

```
frontend/
├── index.html / package.json / vite.config.js
├── electron/
│   ├── main.cjs                    # maximize/unmaximize 时 dispatch resize 事件
│   └── preload.cjs
└── src/
    ├── main.js / App.vue
    ├── api/
    │   ├── index.js / auth.js / plan.js / summary.js / goal.js
    │   ├── parcel.js / courses.js / weather.js / news.js / chaoxing.js
    │   ├── chat.js                 # AI 对话接口
    │   └── music.js                # 网易云音乐接口
    ├── stores/
    │   ├── user.js                 # 用户认证态
    │   └── weatherState.js         # 全局天气共享状态（weatherType/weatherShort/weatherTemp）
    ├── router/
    │   └── index.js                # /report /summary /goals /life /chat /settings
    ├── styles/
    │   └── global.css
    ├── composables/
    │   ├── useAsync.js / useHomeData.js / useGoals.js
    │   ├── useParcels.js / useSummary.js
    │   └── useMusic.js             # 音乐播放状态管理
    ├── views/
    │   ├── LoginView.vue / HomeView.vue / SummaryView.vue
    │   ├── GoalsView.vue / LifeView.vue / SettingsView.vue
    │   └── ChatView.vue            # AI 对话独立页面
    └── components/
        ├── shared/
        │   ├── CrtFrame.vue / PixelButton.vue / SkeletonCard.vue
        │   ├── ErrorBlock.vue / EmptyState.vue
        │   └── SceneBackground.vue  # 动态背景（weatherType 驱动 + rain canvas + pixel cat）
        ├── layout/
        │   ├── BottomNav.vue
        │   └── MusicBar.vue        # 底部音乐播放器常驻
        ├── home/
        │   ├── HeroSection.vue / InfoGrid.vue / CourseTimeline.vue
        │   ├── DeepInsight.vue / FocusList.vue
        │   ├── HomeRightPanel.vue   # 天气独立刷新 + 像素快递图标 + 分割线间距
        │   ├── HomeSkeleton.vue
        │   └── ChatInline.vue      # Today 页内嵌 AI 对话框
        ├── goals/
        │   └── GoalForm.vue / GoalList.vue / GoalItem.vue
        ├── parcel/
        │   └── ParcelForm.vue / ParcelList.vue / ParcelItem.vue
        └── summary/
            └── SummaryForm.vue / SummaryList.vue / SummaryItem.vue
```

---

## 核心接口约定

### 前端 → Java（全部走 /api 前缀 + JWT Bearer token）

```
POST /api/user/register              {username, password}
POST /api/user/login                 {username, password}        → {token, userId, username}
GET  /api/plan?location=南昌&forceRefresh=false
GET  /api/weather?location=北京&lat=&lng=
     → {location, weather, condition_text, condition_icon}
     condition_text: 和风天气实时文字（晴/多云/阴/雨/雪等），前端用于驱动 SceneBackground 场景
GET  /api/news?goals=&summary=
GET  /api/chaoxing/tasks
GET  /api/courses?week=
POST /api/courses/browser-import
DELETE /api/courses
POST /api/summary                    {userId, content, moodScore}
GET  /api/summary?userId=1
POST /api/goal                       {userId, type, content, ...}
GET  /api/goal?userId=1
POST /api/parcel                     {userId, trackingNo, carrier, remark}
GET  /api/parcel?userId=1
DELETE /api/parcel/{id}
POST /api/chat                       {userId, message, context}  → {reply}
GET  /api/music/recommend
GET  /api/music/like?uid=xxx
GET  /api/music/url?id=xxx
```

### Java → Python 调用

```
POST http://localhost:8000/generate-plan
{
  "user_id": "123",
  "yesterday_summary": "...",
  "goals": [...],
  "location": "南昌",
  "parcels": [{"tracking_no": "xxx", "carrier": "顺丰", "remark": "耳机"}]
}
→ { "plan": "...", "priorities": [...], "warnings": [...], "parcels": [...] }

POST http://localhost:8000/chat
{
  "message": "用户输入",
  "context": { "today_plan": "...", "courses": [...], "goals": [...], "recent_summaries": [...] }
}
→ { "reply": "..." }

GET  http://localhost:8000/weather?location=北京&lat=28.68&lng=115.85
→ {location, weather, condition_text, condition_icon}
GET  http://localhost:8000/news?goals=&yesterday_summary=
GET  http://localhost:8000/chaoxing/tasks
GET  http://localhost:8000/courses?week=
```

---

## 天气 → 场景数据流

```
和风天气 API (now.text = "小雨", now.icon = "305")
    ↓
Python tools/weather.py  _fetch_weather_now() → (formatted, condition_text, condition_icon)
    ↓
Python routers/weather.py  → {location, weather, condition_text, condition_icon}
    ↓
Java LifeAgentClient.callWeather()  → Map{weather, condition_text, condition_icon}
    ↓
Java LifeController.getWeather()  → ResponseEntity<Map>
    ↓
前端 useHomeData.js loadWeather()
    └─ deriveWeatherType(condition_text || fmt.text):
       包含"雪"→snowy  包含"雨"→rainy  包含"云"/"阴"→cloudy  包含"晴"→sunny
    └─ 写入 stores/weatherState.js（全局共享）
    ↓
App.vue  :weather-type="weatherType"
    ↓
SceneBackground.vue  weatherType prop 驱动：
   rainy   → 斜线雨丝 canvas (z-index:1) + 窗玻璃水珠
   snowy   → 雪花粒子
   cloudy  → 云层压暗 + 城市降亮度
   sunny   → 无粒子，正常场景
```

---

## 数据库表（核心）

```sql
CREATE TABLE user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL COMMENT 'BCrypt加密',
    wechat_work_id VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_summary (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    summary_date DATE NOT NULL,
    content TEXT NOT NULL,
    mood_score TINYINT COMMENT '精力评分 1-5',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_date (user_id, summary_date)
);

CREATE TABLE goal (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    type ENUM('weekly', 'monthly') NOT NULL,
    content VARCHAR(500) NOT NULL,
    start_date DATE,
    end_date DATE,
    status ENUM('active', 'done') DEFAULT 'active',
    INDEX idx_user_status (user_id, status)
);

CREATE TABLE parcel (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    tracking_no VARCHAR(100) NOT NULL,
    carrier VARCHAR(50),
    remark VARCHAR(100),
    status VARCHAR(200),
    track_details TEXT COMMENT '完整物流轨迹JSON',
    last_checked DATETIME,
    is_delivered BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_delivered (user_id, is_delivered)
);

CREATE TABLE daily_plan (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    plan_date DATE NOT NULL,
    content TEXT NOT NULL,
    raw_data JSON COMMENT '多源数据快照',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_plan_date (user_id, plan_date)
);
```

---

## 当前进度

- [x] 项目初始化
- [x] Python FastAPI 基础框架
- [x] 天气 API 接入（和风天气，含 condition_text/condition_icon 透传）
- [x] LLM API 接入（DeepSeek，OpenAI 兼容格式）
- [x] Java 业务层基础框架（Spring Boot 3 + MyBatis Plus）
- [x] Java → Python 调用链跑通（RestTemplate + 降级）
- [x] 学习通抓取（模拟登录 + 课程列表抓取）
- [x] 教务系统课表抓取（Playwright 浏览器自动化 + HTML 表格解析 + 周次过滤）
- [x] JWT 登录鉴权（jjwt 0.12 + BCrypt + 拦截器方式）
- [x] 多源数据融合（天气 + 课表 + 学习通 + 新闻 + 快递 + 昨日总结 + 长期记忆 → LLM Prompt）
- [x] 前端基础页面（Vue 3 多页面 + 侧边栏导航 + Electron 桌面端）
- [x] Electron 桌面端接入（无框窗口 1440×900，透明 Vibrancy，IPC 窗口控制 + maximize resize 适配）
- [x] 前端多页面完善（今日汇报 / 每日总结 / 目标管理 / 生活 / 设置）
- [x] 新闻模块（多源拉取 + LLM 关键词提取 + 个性化筛选）
- [x] 快递查询模块（快递100 API，16 家快递公司映射，签收自动标记）
- [x] 长期记忆 MVP（精力趋势 + 规划vs总结对比 + 目标进度，MySQL 只读查询）
- [x] 生活模块 Java 代理（天气/新闻/课表/学习通全部通过 Java /api/* 转发）
- [x] 前端 sessionStorage 日期感知缓存（含 weatherType 缓存）
- [x] Python 独立路由拆分（weather/news/chaoxing 各有独立 Router）
- [x] **UI 像素风**（完整实现：侧边栏/导航/标题栏/卡片像素风样式）
- [x] **动态背景场景**（SceneBackground.vue，weatherType + 时间段双维度驱动）
- [x] **像素猫**（16×16 圆润坐姿，2×2 耳朵，白色+黑瞳孔眼睛，尾巴环绕，idle 1.2s 循环）
- [x] **Canvas 雨雪粒子**（rain: 独立高分辨率 canvas，15° 斜线雨丝 100 条 + 窗玻璃水珠 10 个；snow: 像素雪花）
- [x] **天气场景数据驱动**（condition_text 从和风 API → Python → Java → 前端 deriveWeatherType → App.vue weatherType prop，无硬编码）
- [x] **天气独立刷新**（HomeRightPanel 刷新按钮，独立调用 /api/weather，不与规划缓存耦合）
- [x] **背景压暗**（天空渐变冷色 shift，城市暗色叠加，vignette 增强）
- [x] **内容区半透明遮罩**（左侧主内容区 linear-gradient 暗色遮罩）
- [x] **导航选中态增强**（2px 竖线 + rgba 填充 + #e07030 文字）
- [x] **ONLINE 状态点闪烁动画**（2s 循环，opacity 1→0.2→1）
- [x] **每日重点 5 条**（planner_prompt 要求 4~5 条，前端展示 slice(0,5)）
- [x] **全局字体调整**（导航 13px，内容 13px，次要 11px，Hero 标题 zpix 优先统一字号）
- [x] **右侧面板间距**（20px 间距 + 分割线 + 新闻 line-height:1.8）
- [x] **快递像素图标**（16×16 SVG 纸箱，替换掉加载失败的 img）

### 待办事项

- [ ] **AI 对话模块**（ChatView.vue + ChatInline.vue + /api/chat 接口全链路）
- [ ] **总结 AI 回复**（SummaryView 提交后自动触发 AI 情绪反馈，展示在总结卡片下方）
- [ ] **网易云音乐接入**（NeteaseCloudMusicApi + MusicBar.vue 常驻底部）
- [ ] **企业微信推送落地**（早 8 点规划摘要 + 晚 9 点总结提醒）
- [ ] **晚间打卡 / 总结引导**（21:00 推送，基于早间 plan 反向填充预填模板）
- [ ] **长期记忆第二阶段**（TF-IDF 关键词提取 + LLM 行为模式分析）
- [ ] **周报 / 月报生成**（周日 22:00 聚合本周总结 + 目标进度 → LLM 生成）
- [ ] 定时任务完善（ScheduleService 方法体为空，待填充）
- [ ] 缓存升级（Redis 替代 sessionStorage，支持跨设备）
- [ ] 向量数据库引入（第三阶段）

---

## 前端 UI 风格规范

### 整体基调

Liminal pixel art 风格，参考 Undertale / 独立游戏美术。
风格关键词：liminal pixel art interior · tiny warm-colored creature · nostalgic retro ambiance · CRT monitor glow · emotional isolation · minimalist composition · muted grayscale palette with orange focal point · dreamlike stillness · quiet midnight atmosphere

### 色彩变量

```css
:root {
  --bg: #080604;
  --orange: #e07030;
  --orange-dim: #8b4a1f;
  --card: rgba(14, 9, 5, 0.72);
  --card-border: rgba(224, 112, 48, 0.13);
  --text: #c8b89a;
  --text-dim: #6b5a48;
  --nav-bg: rgba(6, 4, 3, 0.82);
}
```

### 字体

- 标题/Hero：`var(--font-body)` = 'zpix', 'Press Start 2P', monospace（zpix 优先，中英文字号一致）
- 导航/Logo：`var(--font-display)` = 'Press Start 2P', 'zpix', monospace
- 正文/数据/内容：`var(--font-body)`
- 中文密集区（新闻/规划/课程）：`var(--font-content)` = 'zpix', monospace
- 字号：导航 13px，内容 13px，次要信息 11px，Hero 标题 clamp(26px, 2.4vw, 34px)
- 所有图形元素：`image-rendering: pixelated`

### 动态背景（SceneBackground.vue，全局组件）

双 canvas 架构：

**主场景 canvas（320×180 内部分辨率，CSS 缩放，z-index:0）**
- 天空渐变（深紫/灰冷色调，dawn/dusk 不再用暖橙红）
- 城市剪影 + 暗色叠加层（rgba(4,3,2,0.35)）
- 路灯橙色光晕（唯一保留的暖色点缀）
- 月亮/太阳像素块 + 星星闪烁
- 窗框 + 窗帘 + 窗台
- 像素猫（16×16，坐姿，2×2 圆耳朵，白色+黑瞳孔眼睛，尾巴环绕，idle 1.2s bob）
- 晕染遮罩（vignette 0.60）
- CRT 扫描线（CSS，opacity 0.06）

**天气效果 canvas（全窗口原生分辨率，z-index:1，pointer-events:none）**
- rainy：100 条 15° 斜线雨丝（1px 宽，12-32px 长）+ 10 个窗玻璃水珠（细长，极慢下滑）
- snowy：像素雪花粒子（在主 canvas 上）
- cloudy：云层方块 drifting + 天空额外压暗
- sunny：无叠加效果

**场景切换**
- weatherType prop 数据驱动（来自和风 API condition_text）
- weatherType 变化时：主 canvas opacity 0.5s fade → 重绘 → fade in
- rain canvas：rainy 时启动独立 rAF loop，非 rainy 时停止并 clear
- Electron 最大化：监听 window.resize + main.cjs dispatch resize 事件

时间段（独立维度，与天气叠加）：
- 清晨（5:00–8:00）：深紫→暗紫渐变
- 白天（8:00–17:00）：灰蓝天空
- 傍晚（17:00–20:00）：深紫→暗红渐变
- 深夜（20:00–5:00）：纯黑夜空 + 月亮 + 星星

### 布局结构

- 自绘标题栏（32px）：三点按钮 + 项目名 + 日期天气
- 左侧导航（160px）：Logo + 导航项（今日/日记/目标/生活/设置）+ ONLINE 状态（绿点闪烁动画）
- 主内容区：左侧半透明遮罩 gradient，城市背景从右侧自然透出
- 底部音乐播放器常驻（44px，左起 160px）

### 卡片规范

```css
.card {
  background: rgba(14, 9, 5, 0.72);
  border: 1px solid rgba(224, 112, 48, 0.13);
  backdrop-filter: blur(8px);
  position: relative;
}
.card::after {
  content: '';
  position: absolute;
  top: 0; left: 15%; right: 15%; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(224,112,48,0.3), transparent);
}
```

### Electron 窗口

- 尺寸：1440×900（最小 1024×680），`frame: false`，透明背景，macOS Vibrancy
- 开发：`http://localhost:3000`；生产：`dist/index.html`（`base: './'`）
- 入口：`frontend/electron/main.cjs` + `preload.cjs`，CommonJS
- 最大化适配：main.cjs 监听 maximize/unmaximize 事件 dispatch window.resize；背景 `100vw×100vh`；`html/body { background: #080604 }` 兜底

---

## AI 对话模块规范

### 定位

知道用户所有上下文的私人助手，不是套壳聊天框。

### 系统 Prompt 注入内容

```
你是用户的个人助手，以下是他今天的状态：
- 今日课程：{courses}
- 待完成作业及截止日期：{tasks}
- 本周/本月目标：{goals}
- 今日规划：{today_plan}
- 最近3天总结（如有）：{recent_summaries}
请根据以上信息回答用户的问题，给出有针对性的建议。
```

### 两个入口

1. **Today 页内嵌（ChatInline.vue）**：规划卡片下方，上下文最完整
2. **Chat 页独立（ChatView.vue）**：左侧导航 Chat 入口，保留历史记录

### 总结提交后 AI 回复

用户在日记页提交总结后自动调用 `/api/chat`，AI 回复展示在总结卡片下方：
- 认可今天做到的事
- 温和指出明天可注意的点
- 语气像了解你的朋友，不说教

---

## 音乐模块规范

### 数据源

NeteaseCloudMusicApi（开源：Binaryify/NeteaseCloudMusicApi），本地 Node 服务。

### 接口（通过 Java /api/music/* 代理）

```
GET /api/music/recommend   → 每日推荐列表
GET /api/music/like        → 喜欢的音乐列表
GET /api/music/url?id=xxx  → 播放链接
```

### UI（MusicBar.vue）

高度 44px，底部常驻，左起 160px。内容：音符图标 + 歌名 + 艺人 + 上一首/播放/下一首 + 进度条 + 时间。

注意：NeteaseCloudMusicApi 为逆向接口，仅供个人使用，不可商用。

---

## 新增功能模块说明

### 个性化新闻（tools/news.py）

LLM 关键词提取 → 多源新闻拉取 → LLM 个性化筛选（3~5 条）。
环境变量：`NEWS_API_KEY`、`NEWS_API_URL`，未配置时降级返回空数据。

### 快递查询（tools/parcel.py）

快递100 API，支持 16 家快递公司，签收后自动标记 `is_delivered = true`。
环境变量：`KUAIDI100_CUSTOMER`、`KUAIDI100_KEY`。

### 长期记忆分析（agents/memory.py）

三项并行查询（asyncio.gather）：精力趋势 + 规划vs总结对比 + 目标进度。数据库不可用时自动降级。

### 生活模块 Java 代理

天气/新闻/课表/学习通全部通过 Java `/api/*` 转发，统一 JWT 鉴权。
天气接口额外透传和风 `condition_text`/`condition_icon`，供前端 SceneBackground 场景驱动。

### 前端缓存策略

sessionStorage 按日期分桶，跨天自动失效，支持 `forceRefresh` 强制刷新。
weather 缓存中包含 `weatherType` 字段，旧缓存无此字段时从 text 降级推导。

### Canvas 雨雪粒子系统

- rain：独立全窗口高分辨率 canvas，rAF 驱动，15° 斜线 stroke 雨丝（非方块），
  窗玻璃细长水珠缓慢下滑，weatherType === 'rainy' 时启动，否则停止清空
- snow：主场景 canvas 上 35 个像素雪花，低帧率循环

### 像素猫

SceneBackground 窗台上的 16×16 像素猫：
- 颜色：`#e07030` 主体 / `#c05820` 阴影
- 外观：圆头、2×2 圆润小耳、白色眼白 + 黑色瞳孔、身体等宽、4 条短腿、尾巴右绕
- 动画：idle bob translateY 0→-2px（1.2s cycle）、随机眨眼（~200 ticks）
- 路灯橙光 wash 叠加

---

## 开发规范

- Python 函数加类型注解
- 每个抓取工具单独一个文件，互不依赖
- Java 调用 Python：连接超时 5s，读取超时 45s，失败返回降级数据
- Prompt 模板统一放 `agent_service/prompts/`，不硬编码在业务代码里
- 敏感信息全部走环境变量，不进代码
- 每个实现阶段结束后写 markdown 文档到 `docs/`
- 所有 `httpx.AsyncClient()` 必须加 `trust_env=False`
- **天气场景严格数据驱动**：weatherType 必须从和风 API condition_text 推导，不允许硬编码
- **Canvas 粒子不用 DOM**：雨雪效果全部在 canvas 内完成，pointer-events:none，不拦截点击
- **前端跨组件状态**：天气共享状态走 `stores/weatherState.js`，App.vue 和 useHomeData 都引用同一 ref

---

## 注意事项

- 学习通/教务抓取属于模拟登录，账号密码本地存储，**不要上传 GitHub**
- `.env` 文件加入 `.gitignore`
- 教务抓取最终方案是 Playwright 浏览器自动化，纯 HTTP CAS 方案已被 VPN JS shell 页面阻断
- `SEMESTER_START` 环境变量配置学期第一周周一日期（如 `2026-03-09`）
- 向量数据库选型待第三阶段再定
- **httpx 代理隔离：** 所有 `httpx.AsyncClient()` 必须加 `trust_env=False`，`main.py` 启动时主动清除代理环境变量
- **Windows Playwright 兼容性：** uvicorn 去掉 `--reload` 或加 `--loop asyncio`；`main.py` 强制设置 `WindowsProactorEventLoopPolicy`
- **启动顺序：** ① MySQL → ② Python（8000）→ ③ Java（8080）→ ④ 前端（3000）或 Electron
- NeteaseCloudMusicApi 为逆向接口，仅供个人使用，不可商用
