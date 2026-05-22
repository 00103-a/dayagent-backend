# DayAgent 移动端设计文档

**日期**: 2026-05-19
**状态**: 已确认

---

## 1. 概述

将 DayAgent 扩展至移动端（Android + iOS），后端 Java + Python 全部复用，前端用 Expo (React Native) 从零构建，保留像素 liminal 美学但适配移动性能约束。

## 2. 技术选型

| 层 | 选择 | 理由 |
|---|---|---|
| 框架 | Expo SDK 54 + React Native | 原生推送、OTA 热更新、云端打包 |
| 语言 | TypeScript 严格模式 | 复用现有 TS 类型体系 |
| 路由 | expo-router (文件路由) | Expo 官方推荐，4.0+ 稳定 |
| 状态管理 | Zustand | 轻量、TS 友好、无 Provider 嵌套 |
| HTTP | axios + 拦截器 | 与现有前端 API 层代码可部分迁移 |
| 推送 | Expo Push Notifications | 免费、跨平台 |
| 构建 | EAS Build | 云端打包，Windows 上也能出 IPA |

后端完全不动。移动端通过 `http://<server>:8080/api/*` 调用现有 Java 接口。

## 3. 页面结构

```
app/
  _layout.tsx              → 根布局，加载字体 + 主题 Provider
  (tabs)/
    _layout.tsx            → 自定义 BottomTabBar
    today.tsx              → 今日（Hero + 规划 + 课表 + 新闻 + 昨日）
    diary.tsx              → 日记（写总结 + AI 反馈）
    life.tsx               → 生活（课表 + 快递 + 新闻聚合）
    goals.tsx              → 目标管理
    settings.tsx           → 设置
  chat.tsx                 → AI 对话独立页（从 today 跳转）
```

## 4. 今日页三态设计

### 4.1 未生成态（清晨首次打开）
- Hero 区：日期 + 天气 + 像素猫 + "◆ 生成今日行动规划"按钮
- 下方卡片区：虚线空白占位
- 猫 idle bob 动画，眼睛看着按钮方向

### 4.2 加载态
- 按钮区域替换为进度指示
- 分步展示：天气 → 课表 → 作业 → 新闻 → 快递 → LLM 生成
- 像素逐格填充进度条

### 4.3 已生成态
- Hero 精简为一行：天气 + 日期 + "刷新"文字按钮
- 规划卡片展开（4~5 条优先级 + warnings + 快递状态）
- 下方可滚动卡片：课表 timeline → 新闻推荐 → 昨日回顾
- 底部内嵌 AI 对话输入框（简单模式，点击展开到 chat 页）

## 5. 组件清单

| 组件 | 描述 | 复用 |
|---|---|---|
| PixelCat | 24×24 像素猫 SVG，idle bob + 眨眼 | 全局 |
| WeatherHero | 天气 + 日期 + 猫 + 生成按钮容器 | today |
| PlanCard | 规划优先级列表 + warnings | today |
| CourseTimeline | 竖线 + 圆点课表时间轴 | today, life |
| PixelCard | 通用 2px 边框卡片 wrapper | 全局 |
| PixelButton | 8-bit 按钮（2px 边框 + hover glow） | 全局 |
| ScanlineOverlay | 卡片内 2px CRT 扫描线纹理 | 全局 |
| GenerateButton | 生成规划 CTA + 加载进度 | today |
| BottomTabBar | 5 图标像素风底部导航 | 全局 |
| SummaryForm | 心情评分 + 完成勾选 + 文本输入 | diary |
| AIFeedback | AI 回复气泡 | diary, today |

## 6. 色彩与主题

完全继承桌面端配色体系：

```typescript
const theme = {
  bg: '#080604',
  orange: '#e07030',
  orangeDim: '#8b4a1f',
  card: 'rgba(14, 9, 5, 0.72)',
  cardBorder: 'rgba(224, 112, 48, 0.13)',
  text: '#c8b89a',
  textDim: '#6b5a48',
  navBg: 'rgba(6, 4, 3, 0.82)',
};
```

字体：`zpix` 优先，降级 `monospace`。所有图形 `image-rendering: pixelated`（React Native 中用 `resizeMode` 模拟）。

## 7. 移动端适配决策

| 桌面端 | 移动端 | 原因 |
|---|---|---|
| Canvas 雨雪粒子 | CSS 渐变 + keyframe | 省电、性能 |
| CRT 扫描线全屏 | 仅卡片内纹理 | 移动屏幕小，全屏太干扰 |
| 自绘标题栏 | 系统状态栏 | 移动端无此概念 |
| 电子窗框/窗帘 | 移除 | 手机无"窗"的隐喻 |
| 像素猫 16×16 | 像素猫 24×24 | 屏幕小需放大 |
| 侧边导航 160px | 底部 Tab 栏 | 移动端标准交互 |

## 8. 不做（YAGNI）

- 音乐模块（待桌面端验证后再说）
- Electron IPC / 窗口控制
- Canvas 粒子系统
- 透明 Vibrancy（移动端无此能力）
- 学习通 Playwright 浏览器抓取在移动端（仅展示后端已抓取的数据）

## 9. 后端依赖

所有 API 已存在，移动端只做调用：

| 接口 | 用途 |
|---|---|
| POST /api/user/login | 登录 |
| GET /api/plan?forceRefresh= | 获取/刷新规划 |
| GET /api/weather | 天气 |
| GET /api/courses?week= | 课表 |
| GET /api/news | 新闻推荐 |
| GET /api/chaoxing/tasks | 学习通作业 |
| GET /api/parcel | 快递列表 |
| POST /api/summary | 提交总结 |
| GET /api/summary | 获取总结历史 |
| POST /api/goal / GET /api/goal | 目标 CRUD |
| POST /api/chat | AI 对话 |

## 10. 测试方法

- Expo Go 扫码开发（`npx expo start`）
- EAS Build 出 APK 安装测试
- 后端部署到可访问的 IP，手机连同一网络测试
