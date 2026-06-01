# DayAgent 桌面管家 — 纯软件版设计文档

> 日期：2026-06-01 | 状态：设计中 | 预算：0 元

---

## 1. 项目定位

把 DayAgent 从一个"打开才用"的网页，变成一个**常驻桌面的智能管家**。它像住进电脑里的小助手，有自己的"性格"（像素猫），能感知环境、主动提醒、聊天对话。

三步走：
1. **先纯软件**（0 元）— IoT 全链路 + 桌面管家体验
2. **加 ESP32 + 传感器**（+28 元）— 真实环境数据
3. **有旧手机就当专用屏幕**（+10 元支架）— 物理分离显示

本文档聚焦第一步。

---

## 2. 核心体验

### 2.1 桌面常驻

Electron 窗口可以最小化到系统托盘，后台持续运行。到点主动弹窗提醒，不被动等用户打开。

### 2.2 环境感知

Python 脚本模拟传感器（温度/湿度/CO₂/光照/PM2.5），数据经 MQTT → InfluxDB → LLM 分析，生成环境建议。后续换 ESP32 只需改数据来源。

### 2.3 语音交互

电脑麦克风 + 扬声器即可：
- 早 8 点自动语音播报："早上好，今天 10 点有课，外面 26°C 晴天"
- 可选：语音唤醒词 + 对话（第三阶段）

### 2.4 AI 聊天

已有 Chat 功能融入桌面体验，随时唤起对话框和管家聊天。

---

## 3. 技术架构

```
[Python Sensor Simulator]       ← 模拟 5 种传感器，每 30s 生成
       │ MQTT
       ▼
[Mosquitto Broker]              ← Docker 容器，本地 localhost
       │
       ▼
[Spring Boot + Paho]            ← 订阅 MQTT → InfluxDB + MySQL
       │                           WebSocket 推前端
       ├──→ InfluxDB            ← 时序数据
       ├──→ MySQL               ← 设备/告警配置
       └──→ WebSocket
       │
       ▼
[FastAPI]                       ← 查 InfluxDB → LLM 分析 → API
       │
       ▼
[Vue 3 + Electron]              ← 桌面端：环境页面 + 聊天 + 规划 + 托盘
       │
       ├── 系统托盘              ← 后台运行，右键菜单
       ├── 定时提醒              ← Electron main process 定时器
       └── 语音 TTS              ← 调用系统 TTS / Edge-TTS
```

### 所有服务都跑在一台电脑上

Docker 容器：MySQL + InfluxDB + Mosquitto
本机进程：Spring Boot (8080) + FastAPI (8000) + Vue/Electron (3000)

---

## 4. 传感器模拟器

（沿用之前 IoT 设计文档第 3 节的完整设计）

- 5 种传感器：温度/湿度/光照/CO₂/PM2.5
- 数据有规律但不死板（正弦波 + 随机噪声 + 特殊事件）
- 文件：`agent_service/simulator/sensor_simulator.py`
- 每 30 秒发一次 MQTT 消息
- 后续换 ESP32 时消息格式完全不变

---

## 5. MQTT 消息设计

（沿用之前 IoT 设计文档第 4 节）

Topic: `sensors/sim-01/readings`

```json
{
  "device_id": "sensor-sim-01",
  "timestamp": "2026-06-01T10:30:00",
  "temperature": 26.3,
  "humidity": 68.5,
  "co2": 1240,
  "light": 520,
  "pm25": 35.2
}
```

QoS = 0，不保留消息。

---

## 6. Spring Boot 接入

（沿用之前 IoT 设计文档第 5 节，完全相同）

新增文件：
- `MqttConfig.java` — Paho 客户端配置
- `MqttSubscriber.java` — 接收 MQTT → 调 Service
- `SensorDataService.java` — 写 InfluxDB + MySQL
- `SensorController.java` — REST API
- `SensorWebSocketHandler.java` — WebSocket 实时推送

---

## 7. FastAPI AI 分析层

（沿用之前 IoT 设计文档第 6 节）

两层分析：
- 规则检测（不耗 LLM）：CO₂>1500、温度>30°C 等即时告警
- LLM 深度分析（~10 分钟一次）：结合传感器数据 + DayAgent 上下文

---

## 8. 桌面管家增强（Electron 端新增）

### 8.1 系统托盘

```
托盘图标：像素猫脸（16x16）
右键菜单：
  - 显示主窗口
  - 今日播报
  - 快速聊天
  - 退出
```

### 8.2 定时播报

Electron main process 用 `node-cron` 定时：
- 早 8:00：调用 `/api/plan` → TTS 播报"今天X节课，温度X°C，X条待办"
- 晚 21:00：弹窗提醒写总结

TTS 方案：Edge-TTS（免费，中文效果好），Python 脚本生成 mp3 → Electron 播放。

### 8.3 通知弹窗

环境告警通过系统通知推送：
- "CO₂ 偏高，建议开窗通风"
- "检测到光线偏暗，注意护眼"

---

## 9. Vue 前端新增

### 9.1 环境页面（EnvironmentView.vue）

- 5 个传感器数值卡片（WebSocket 实时更新）
- ECharts 趋势折线图（可切换 1h/6h/24h）
- AI 环境洞察卡片
- 左侧导航新增"环境"入口

### 9.2 管家对话（增强已有 ChatInline.vue）

在 Today 页面底部，上下文自动注入当天传感器数据。

---

## 10. 项目结构总览

### 新增文件（约 17 个）

```
agent_service/
├── simulator/
│   └── sensor_simulator.py           🆕
├── routers/
│   └── environment.py                🆕
├── agents/
│   └── sensor_analysis.py            🆕
└── tools/
    └── influx_client.py              🆕

business-service/src/main/java/com/dayagent/
├── config/
│   └── MqttConfig.java               🆕
├── mqtt/
│   └── MqttSubscriber.java           🆕
├── service/
│   └── SensorDataService.java        🆕
├── controller/
│   └── SensorController.java         🆕
├── websocket/
│   └── SensorWebSocketHandler.java   🆕
└── entity/
    └── SensorDevice.java             🆕

frontend/src/
├── views/
│   └── EnvironmentView.vue           🆕
├── api/
│   └── sensor.js                     🆕
├── components/environment/
│   ├── SensorCard.vue                🆕
│   ├── SensorChart.vue               🆕
│   └── AIInsightCard.vue             🆕
├── stores/
│   └── sensorState.js                🆕
└── router/
    └── index.js                      ✏️ 新增 /environment

frontend/electron/
    └── main.cjs                      ✏️ 新增托盘 + 定时器 + 通知

docker/
    └── docker-compose.yml            ✏️ 新增 Mosquitto + InfluxDB
```

---

## 11. 降级策略

| 故障 | 处理 |
|------|------|
| MQTT Broker 挂了 | Paho 自动重连；前端显示"传感器离线" |
| InfluxDB 不可用 | 降级写 MySQL，FastAPI 读 MySQL |
| LLM 调用失败 | 仅显示规则告警，AI 洞察区显示"分析暂不可用" |
| 模拟器停了 | 前端保持最后值，标记"数据过期" |
| Docker 未启动 | 后端启动时检测，打 warn 日志，相关功能降级 |

---

## 12. 实施计划（5 天纯软件 + 可选硬件）

| 天 | 内容 | 状态 |
|----|------|------|
| 1 | MQTT 概念 + Mosquitto + Spring Boot Paho 收到第一条消息 | 纯软件 |
| 2 | Docker 跑 InfluxDB + Python 模拟器写入 + 查询 | 纯软件 |
| 3 | Spring Boot MQTT→InfluxDB + REST API + WebSocket→前端 | 纯软件 |
| 4 | FastAPI 查 InfluxDB + LLM 分析 + ECharts 前端图表 | 纯软件 |
| 5 | docker-compose 全家桶 + Electron 托盘/播报 + 整体联调 | 纯软件 |
| +2 | ESP32 + DHT22 真实传感器（28 元） | 可选硬件 |
| +1 | 旧手机装 DayAgent 移动版做副屏（10 元支架） | 可选硬件 |

---

## 13. 简历描述参考

> 独立设计并实现基于 Spring Boot + MQTT + InfluxDB + FastAPI 的 IoT 智能环境感知系统。通过 Eclipse Paho 订阅传感器数据，InfluxDB 存储时序数据，WebSocket 实时推送。集成 DeepSeek LLM 分析环境数据并结合用户日程上下文生成个性化建议。前端使用 Vue 3 + ECharts 实现传感器趋势可视化，Electron 桌面端支持系统托盘常驻与定时语音播报。
