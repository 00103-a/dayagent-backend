# IoT 环境感知模块 — 设计文档

> 日期：2026-06-01 | 状态：设计中 | 关联项目：DayAgent

---

## 1. 项目定位

给 DayAgent 新增"环境感知"能力。通过 MQTT 协议接入传感器数据（先用 Python 脚本模拟），存入时序数据库，结合 LLM 分析环境数据与用户日程上下文，生成个性化环境建议。前端新增像素风环境监测 Dashboard。

**核心价值**：把 DayAgent 从"查线上数据"升级成"感知物理环境"，让简历同时覆盖 IoT 和 AI 两个方向。

---

## 2. 整体架构

```
[Python Sensor Simulator]          ← 模拟 5 种传感器，每 30s 生成数据
       │ MQTT publish
       ▼
[Mosquitto MQTT Broker]            ← 轻量消息中间件
       │ subscribe
       ▼
[Spring Boot + Eclipse Paho]       ← 接收 MQTT → 写 InfluxDB + MySQL → WebSocket 推送
       │
       ├──→ InfluxDB               ← 时序数据存储（sensor_readings）
       ├──→ MySQL                  ← 设备配置 + 告警阈值 + 告警日志
       └──→ WebSocket → Vue        ← 实时推数值到前端
       │ HTTP
       ▼
[FastAPI AI 分析层]                 ← 查 InfluxDB → 规则告警 + LLM 洞察
       │ HTTP
       ▼
[Vue 3 前端]                       ← 新增"环境"页面：实时卡片 + ECharts 图表 + AI 建议
```

### 新增组件

| 组件 | 用途 | 类型 |
|------|------|------|
| Mosquitto MQTT Broker | 消息中间件，Docker 部署 | 新增 |
| InfluxDB | 时序数据库，存传感器历史数据 | 新增 |
| Eclipse Paho | Spring Boot MQTT 客户端库 | 新增 |
| ECharts | Vue 端图表库，画趋势折线图 | 新增 |

### 复用现有组件

Spring Boot、FastAPI、MySQL、Vue 3、JWT 鉴权、DeepSeek LLM 调用链路全部复用。

---

## 3. 传感器模拟器

### 3.1 设计原则

数据有规律但不死板，模拟真实传感器的行为特征。后续换真实 ESP32 硬件时，只需改数据来源（MQTT 消息格式不变）。

### 3.2 模拟的传感器

| 传感器 | 模拟规律 | 数据范围 |
|--------|----------|----------|
| 温度 | 白天高晚上低，正弦波 + 随机噪声 | 20 ~ 32°C |
| 湿度 | 与温度反向变化 | 40% ~ 90% |
| 光照 | 白天 300-800 lux，夜间 < 50 | 20 ~ 800 lux |
| CO₂ | 持续上升（模拟人在房间呼吸），开窗事件骤降 | 400 ~ 2000 ppm |
| PM2.5 | 基准值 + 随机波动，偶发小高峰 | 10 ~ 80 μg/m³ |

### 3.3 特殊事件

- **开窗通风**：每小时随机触发，CO₂ 快速降至 600，湿度变化
- **下雨天**：湿度飙升 85%+，温度略降，光照 < 100
- **多人聚集**：CO₂ 快速升至 1800+，温度上升 2-3°C

### 3.4 文件位置

```
agent_service/simulator/sensor_simulator.py
```

独立脚本，直接运行 `python sensor_simulator.py` 启动，Ctrl+C 停止。

---

## 4. MQTT 消息设计

### 4.1 消息格式（JSON）

Topic: `sensors/{device_id}/readings`

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

### 4.2 QOS 与保留

- QOS = 0（最多一次），传感器数据允许偶尔丢失
- 不保留消息（Retain = false），只关心最新值

### 4.3 Broker 部署

Mosquitto 通过 Docker 一行启动：

```bash
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto:latest
```

---

## 5. Spring Boot 接入

### 5.1 新增文件

```
business-service/src/main/java/com/dayagent/
├── config/
│   └── MqttConfig.java          # Paho 客户端配置（连接 Mosquitto）
├── mqtt/
│   └── MqttSubscriber.java      # 消息回调 → 解析 JSON → 调用 Service
├── service/
│   └── SensorDataService.java   # 写 InfluxDB + 更新 MySQL 设备状态
├── controller/
│   └── SensorController.java    # REST API: GET /api/sensor/current, GET /api/sensor/history
├── websocket/
│   └── SensorWebSocketHandler.java  # WebSocket 实时推送
└── entity/
    └── SensorDevice.java        # 设备实体，MyBatis Plus 映射
```

### 5.2 数据存储分工

**InfluxDB**（时序数据）：
- measurement: `sensor_readings`
- tags: `device_id`
- fields: `temperature, humidity, co2, light, pm25`
- 保留策略：7 天原始数据 → 1 年降采样

**MySQL**（配置数据）：
- `sensor_device` — 设备 ID、名称、位置、在线状态
- `sensor_alert_config` — 各传感器告警阈值
- `sensor_alert_log` — 告警历史记录

### 5.3 REST API

```
GET /api/sensor/current              → 各传感器最新值
GET /api/sensor/history?range=1h     → 历史数据（供图表）
GET /api/sensor/alerts?limit=10      → 最近告警
```

### 5.4 WebSocket

endpoint: `/ws/sensor`
推送频率：每收到一条 MQTT 消息就推一次（约 30s 间隔）

---

## 6. FastAPI AI 分析层

### 6.1 新增文件

```
agent_service/
├── routers/
│   └── environment.py           # GET /environment/insights
├── agents/
│   └── sensor_analysis.py       # LLM 环境分析逻辑
└── tools/
    └── influx_client.py         # InfluxDB 读写客户端（异步）
```

### 6.2 两层分析

**第一层：规则检测（不耗 LLM token）**

| 条件 | 告警 |
|------|------|
| CO₂ > 1500 ppm | 建议通风 |
| 温度 > 30°C | 高温提醒 |
| 湿度 > 85% | 潮湿提醒 |
| PM2.5 > 75 | 空气质量差 |
| 光照 < 200 lux | 光线偏暗 |

规则检测结果通过 WebSocket 即时推送。

**第二层：LLM 深度分析（定时调用，约 10 分钟一次）**

取最近 1 小时传感器数据，拼上 DayAgent 上下文（当日课表、待完成作业、本周目标、今日规划），发送给 DeepSeek：

```
你是环境助手。过去1小时传感器数据：
温度26→28°C上升，CO2从800→1400上升，湿度65%，PM2.5正常。
用户今天下午2点有课（教学楼步行10分钟）。
请给出1-2条环境建议，语气友好，每条≤30字。
```

LLM 回复示例：
> "CO2偏高，课前开窗通风10分钟再出门吧 ☁️"

### 6.3 API（调用链路）

遵循现有架构规范，前端通过 Java 代理调用 Python：

```
前端 GET /api/environment/insights?forceRefresh=false
    → Java LifeController / SensorController 代理转发
    → Python GET /environment/insights?user_id=1
        → 查 InfluxDB 最新数据
        → 规则检测 + LLM 分析
    → 返回:
    {
        "alerts": [
            {"type": "co2_high", "message": "CO2偏高，建议通风", "severity": "warning"}
        ],
        "ai_insights": ["CO2偏高，课前开窗通风10分钟再出门吧 ☁️"],
        "current_readings": {"temperature": 26.3, "humidity": 68.5, ...}
    }
```

Java 端连接超时 5s，读取超时 45s（与现有 Agent 调用保持一致），失败返回降级数据（仅规则告警，AI 洞察为空）。

---

## 7. Vue 前端 Dashboard

### 7.1 新增文件

```
frontend/src/
├── views/
│   └── EnvironmentView.vue      # 环境监测主页面
├── api/
│   └── sensor.js                # API 调用封装
├── components/environment/
│   ├── SensorCard.vue           # 单个传感器数值卡片（像素风）
│   ├── SensorChart.vue          # ECharts 趋势折线图组件
│   └── AIInsightCard.vue        # AI 洞察卡片
├── router/
│   └── index.js                 # 新增 /environment 路由
└── stores/
    └── sensorState.js           # 传感器全局状态
```

### 7.2 页面布局

```
┌─────────────────────────────────────────────────────┐
│  [温度卡片] [湿度卡片] [CO2卡片] [光照卡片] [PM2.5卡片]  │  ← 实时数值 + 变化趋势箭头
├──────────────────────────┬──────────────────────────┤
│                          │                          │
│   ECharts 趋势折线图      │   🧠 AI 环境洞察          │  ← 像素风卡片
│   (可切换 1h/6h/24h)     │   最新 LLM 建议           │
│                          │   更新时间戳              │
└──────────────────────────┴──────────────────────────┘
```

### 7.3 导航变更

左侧导航新增一项（绿色调以区别于现有橙色）：

```
🛰️ 环境   ← 新增，放在"生活"上方
```

### 7.4 实时更新

- 数值卡片：WebSocket 推送自动更新，无需手动刷新
- AI 洞察：定时轮询（10 分钟一次），或手动点击刷新按钮
- 图表：切换时间范围时重新请求 `/api/sensor/history`

---

## 8. 降级与错误处理

| 故障场景 | 处理方式 |
|----------|----------|
| MQTT Broker 挂了 | Spring Boot 自动重连（Paho 内置），前端显示"传感器离线" |
| InfluxDB 不可用 | 降级写 MySQL，数据不丢；FastAPI 查 MySQL 降级 |
| LLM 调用失败 | 仅显示规则告警，AI 洞察区域显示"分析暂不可用" |
| 模拟器停了 | 前端数值卡片保持最后值 + 显示"数据过期"标记 |

---

## 9. 实施计划概览

| 阶段 | 内容 | 预计 |
|------|------|------|
| 1 | 传感器模拟器 + InfluxDB 直写（先不通 MQTT） | 1 天 |
| 2 | Mosquitto 部署 + 模拟器改发 MQTT + Spring Boot 订阅 | 1.5 天 |
| 3 | Spring Boot 数据写入 InfluxDB + MySQL + REST API + WebSocket | 2 天 |
| 4 | FastAPI 规则检测 + LLM 环境分析 | 1.5 天 |
| 5 | Vue 前端 ECharts 图表 + 实时卡片 + AI 洞察 + 导航 | 2 天 |
| **合计** | | **~8 天** |

---

## 10. 环境变量新增

```bash
# MQTT
MQTT_BROKER_URL=tcp://localhost:1883
MQTT_CLIENT_ID=dayagent-spring

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=dayagent
INFLUXDB_BUCKET=sensors
```

---

## 11. 简历描述参考

> 基于 Spring Boot + MQTT + InfluxDB + FastAPI 构建 IoT 智能环境感知系统。通过 Eclipse Paho 订阅传感器数据，InfluxDB 存储时序数据，WebSocket 实时推送。FastAPI 结合 DeepSeek LLM 分析环境数据与用户日程上下文，生成个性化环境建议。前端使用 ECharts 实现传感器趋势可视化 Dashboard。
