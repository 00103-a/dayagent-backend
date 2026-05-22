# 生活页面设计文档

## 概述

将天气、新闻、课表、学习通、快递五个功能模块整合到统一的"生活"页面，替代现有的独立快递页面。每个模块以独立卡片展示，支持独立刷新/操作。

## 页面结构

新路由 `/life`，组件 `LifeView.vue`，5 张卡片垂直堆叠：

```
┌─ 今日天气 ────────────────────────── [刷新] ─┐
│  天气文本                                     │
├─ 个性化新闻 ──────────────────────── [刷新] ─┤
│  · 新闻标题1 — 摘要                           │
│  · 新闻标题2 — 摘要                           │
├─ 我的课表 ──────────── [导入课表] [清空] ────┤
│  周一：1-2节 高等数学 @教学楼A101...            │
├─ 学习通 ──────────────────────────── [刷新] ─┤
│  本学期课程（共 8 门）：...                     │
├─ 我的快递 ───────────────────── [添加快递] ──┤
│  [顺丰] 耳机 — SF1234567890                   │
│    状态展开 → 完整物流时间线                    │
└──────────────────────────────────────────────┘
```

### 四态处理

每个卡片独立处理四态：loading / error / empty / data，使用现有共享组件（SkeletonCard / ErrorBlock / EmptyState）。

## API 变更

### 新增 Java 控制器

所有新接口走 Java 代理到 Python，统一 `/api/` 前缀 + JWT 鉴权。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/weather?location=xx` | 查询城市天气 |
| GET | `/api/news?userId=1` | 获取个性化新闻 |
| GET | `/api/courses` | 查看已导入课表 |
| POST | `/api/courses/browser-import` | 启动浏览器导入课表 |
| DELETE | `/api/courses` | 清空课表 |
| GET | `/api/chaoxing/tasks` | 获取学习通课程 |
| POST | `/api/parcel` | 添加快递（已有） |
| GET | `/api/parcel` | 查快递列表（已有） |
| DELETE | `/api/parcel/{id}` | 删除快递（已有） |

### 课程收拢

现有的 `/courses/*` 直连 Python 的调用改为走 `/api/courses/*` Java 代理。Vite 代理中的 `/courses` 规则可移除。

### Python 侧新增端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/weather?location=xx` | 对外开放的天气查询路由 |
| GET | `/news?userId=1` | 个性化新闻独立路由 |
| GET | `/chaoxing/tasks` | 学习通课程抓取路由 |

课表和快递路由已有，不需要新增。

## 快递轨迹详情

### 数据库

`parcel` 表新增列：

```sql
ALTER TABLE parcel ADD COLUMN track_details JSON COMMENT '完整物流轨迹';
```

### 数据流

1. `/generate-plan` 生成规划时，Python 返回每单快递的 `details` 数组
2. `AgentCallerService` 将 `details` JSON 写入 `track_details` 列
3. 前端点击快递卡片展开轨迹时，从列表中的 `trackDetails` 字段读取（列表接口直接返回）

### 前端

`ParcelItem.vue` 新增展开/折叠箭头，展开后显示时间线：

```
2026-05-18 10:30  已到达北京分拣中心
2026-05-17 08:00  已从深圳发出
2026-05-16 14:00  包裹已揽收
```

已签收的快递默认折叠，可手动展开查看完整轨迹。

## 导航变更

| 变更项 | 原来 | 改为 |
|--------|------|------|
| 底部导航 | "快递" tab | "生活" tab |
| 路由 | `/parcel` | `/life`，旧路由重定向到 `/life` |
| 设置页 | "课表导入"卡片 | 删除该卡片 |

## 前端文件变更

| 文件 | 操作 |
|------|------|
| `src/views/LifeView.vue` | 新建，替代 ParcelView |
| `src/views/ParcelView.vue` | 删除 |
| `src/api/weather.js` | 新建 |
| `src/api/news.js` | 新建 |
| `src/api/courses.js` | 新建（原本内联在 plan.js 里的 importCourses 移出） |
| `src/api/chaoxing.js` | 新建 |
| `src/composables/useParcels.js` | 修改，适配生活页上下文 |
| `src/components/parcel/ParcelItem.vue` | 修改，增加轨迹展开 |
| `src/components/layout/BottomNav.vue` | 修改，"快递" → "生活"，路径改为 `/life` |
| `src/router/index.js` | `/parcel` 重定向到 `/life`，新增 `/life` |
| `src/views/ReportView.vue` | 保留"导入课表"按钮不做改动 |
| `src/views/SettingsView.vue` | 删除"课表导入"卡片 |
| `src/api/plan.js` | 移除 `importCourses` 函数 |

## Java 端变更

| 文件 | 操作 |
|------|------|
| `controller/LifeController.java` | 新建，代理 weather/news/courses/chaoxing |
| `service/LifeAgentClient.java` | 新建，HTTP 调用 Python 新端点 |
| `entity/Parcel.java` | 新增 `trackDetails` 字段 |
| `service/AgentCallerService.java` | 增加 details 写入 track_details 逻辑 |
| `config/WebConfig.java` | 确认 CORS 覆盖新路径 |

## Python 端变更

| 文件 | 操作 |
|------|------|
| `routers/weather.py` | 新建，暴露 `GET /weather?location=xx` |
| `routers/news.py` | 新建，暴露 `GET /news?userId=1` |
| `routers/chaoxing.py` | 新建，暴露 `GET /chaoxing/tasks` |
| `routers/courses.py` | 无变化，已有接口 |
| `routers/plan.py` | 无变化，已有接口 |
| `main.py` | 注册新路由 |
| `tools/parcel.py` | 无需改动，已有 `query_parcels_detailed` 返回 details |

## 实施顺序

1. Python 新增 3 个独立路由（weather / news / chaoxing）
2. Java 新增 LifeController + LifeAgentClient（代理所有模块调用）
3. Java 修改 Parcel 实体 + AgentCallerService（轨迹存储）
4. 前端 API 层 + 新 LifeView + 组件改造
5. 导航和路由调整
6. 清理旧代码（ParcelView、Settings 课表卡片）
