# DayAgent IoT 传感器数据管道 — 完整总结

> 日期：2026-06-07  
> 范围：从 ESP32 烧录到 AI 语音识别之前的所有工作

---

## 一、架构全景

```
┌─────────────────────────────────────────────────────────────────┐
│                        硬件层 (ESP32-S3)                         │
│                                                                 │
│  DHT22 ──温度/湿度──┐                                           │
│                     ├── ESP32-S3 ──WiFi──▶ MQTT (Mosquitto)     │
│  BH1750 ──光照──────┘       │                                    │
│                          ST7789 屏幕 (本地显示)                   │
│                          INMP441 + MAX98357A (音频环回,实验性)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ MQTT (tcp://电脑IP:1883)
┌─────────────────────────────────────────────────────────────────┐
│                       中间件层 (Docker)                          │
│                                                                 │
│  Mosquitto (MQTT Broker)    InfluxDB 2.7 (时序数据库)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      业务层 (Java Spring Boot :8080)             │
│                                                                 │
│  MqttSubscriber → InfluxDBWriter → InfluxDB                     │
│  SensorController ← InfluxDBReader ← InfluxDB                   │
│  LifeController → LifeAgentClient → Python Agent (:8000)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent 层 (Python FastAPI :8000)             │
│                                                                 │
│  /environment/insights → influx_client → InfluxDB → LLM 分析     │
│  /voice/chat (实验) → Whisper STT → DeepSeek → edge-tts          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP
┌─────────────────────────────────────────────────────────────────┐
│                    前端层 (React Native Expo)                    │
│                                                                 │
│  today.tsx → WeatherHero (天气) + SensorPanel (室内环境)         │
│  stores/weather.ts → weatherType 全局状态                        │
│  api/sensor.ts → fetchCurrentSensor / fetchEnvironmentInsights  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、ESP32 硬件

### 2.1 接线

| 模块 | 引脚 | ESP32-S3 | 协议 |
|------|------|----------|------|
| ST7789 屏幕 | SCL | GPIO12 | SPI |
| | SDA/MOSI | GPIO11 | |
| | RES | GPIO10 | |
| | DC/AO | GPIO9 | |
| | CS | GPIO13 | |
| | BLK | GPIO14 | |
| DHT22 温湿度 | DATA | GPIO4 | 单总线 |
| BH1750 光照 | SCL | GPIO6 | I2C |
| | SDA | GPIO7 | |
| INMP441 麦克风 | SCK | GPIO5 | I2S |
| | WS | GPIO15 | |
| | SD | GPIO16 | |
| MAX98357A 功放 | BCLK | GPIO5 | I2S (与麦克风共用时钟) |
| | LRC | GPIO15 | |
| | DIN | GPIO8 | |

**供电：** 所有模块 VCC → 面包板 + 排（3.3V），GND → 面包板 - 排。ESP32 通过 2 根公公线向面包板供电。

### 2.2 开发环境

- **IDE：** VS Code + PlatformIO
- **框架：** Arduino (espressif32 @ 7.0.1)
- **板子：** ESP32-S3-DevKitC-1 (N16R8, 16MB Flash, 8MB Octal PSRAM)
- **关键库：**
  - `Adafruit ST7735 and ST7789 Library` — 屏幕驱动
  - `Adafruit GFX Library` — 图形绘制
  - `DHT sensor library` — DHT22 读数
  - `PubSubClient` — MQTT 客户端

### 2.3 屏幕调试历程

ST7789 1.9 寸 240×320 屏幕调试关键发现：

1. **ESP32-S3 必须显式指定 SPI 引脚：** `SPI.begin(TFT_SCK, -1, TFT_MOSI, TFT_CS)`
2. **SPI 模式：** `SPI_MODE0`
3. **颜色反转：** 此屏幕不需要 `invertDisplay`
4. **硬件复位必要：** RST 脚拉低 10ms → 拉高，等待 120ms 再初始化
5. **TFT_eSPI 库不兼容 S3：** 改用 Adafruit_ST7789

### 2.4 传感器代码核心逻辑

```cpp
// DHT22 — 单总线协议
#include <DHT.h>
DHT dht(4, DHT22);        // 4号脚，DHT22型号
dht.begin();               // 唤醒传感器
float t = dht.readTemperature();  // 读数
float h = dht.readHumidity();

// BH1750 — I2C 协议
#include <Wire.h>
Wire.begin(7, 6);          // SDA=7, SCL=6
Wire.beginTransmission(0x23); // I2C 地址 0x23
Wire.write(0x10);           // 连续高分辨率模式
// 读 2 字节 → 合并 → ÷1.2 = lux

// MQTT 发送
mqtt.publish("dayagent/esp32-s3/sensor/environment", json);
// JSON: {"device_id":"esp32-s3","temperature":25.6,"humidity":54.2,"co2":0,"light":37,"pm25":0}
```

---

## 三、后端数据流

### 3.1 MQTT → InfluxDB（写入链）

```
ESP32 ──MQTT──▶ Mosquitto ──订阅──▶ MqttSubscriber.java
                                        │
                                   saveToInfluxDB(json)
                                        │
                                   InfluxDBWriter.save()
                                        │
                                   InfluxDB (bucket=sensors)
```

**关键文件：**
- `MqttConfig.java` — Paho MQTT 客户端 Bean（`tcp://localhost:1883`，自动重连）
- `MqttSubscriber.java` — 订阅 `dayagent/+/sensor/environment`，解析 JSON，写入 InfluxDB
- `InfluxDBWriter.java` — 通过 influxdb-client-java 6.12.0 写入 Point

### 3.2 InfluxDB → API（读取链）

```
GET /api/sensor/current
        │
   SensorController.java
        │
   InfluxDBReader.queryLatest()
        │
   Flux: from(bucket:"sensors") |> range(start:-5m) |> filter(...) |> limit(1)
        │
   返回 {temperature, humidity, co2, light, pm25}
```

**关键文件：**
- `InfluxDBReader.java` — Flux 查询最新一条 sensor_readings
- `SensorController.java` — 注入 Reader，有数据返回真实值，无数据返回全 null（HashMap 兼容 null）

### 3.3 环境 AI 洞察

```
GET /api/environment/insights
        │
   LifeController → LifeAgentClient → Python /environment/insights
        │
   influx_client.py → InfluxDB (查最近60分钟)
        │
   sensor_analysis.py → DeepSeek LLM (结合课程/目标分析)
        │
   返回 {current_readings, alerts, ai_insights}
```

### 3.4 Docker 配置注意事项

- Mosquitto 端口 **不能** 绑 `127.0.0.1`（只允许本机），必须 `1883:1883`（允许局域网设备连接）
- InfluxDB 初始化：bucket=sensors, org=dayagent, token=dayagent-dev-token

---

## 四、移动端适配

### 4.1 天气板块改造（WeatherHero.tsx）

原来：一行文字堆砌
> "南昌今日天气：阴，温度 31℃，体感温度 32℃，东北风3级，相对湿度59%"

改造后：视觉卡片布局
```
6月5日 · 南昌
阴                    ← 大字天气状况
┌──────┬──────┬──────┬──────┬──────┐
│ 31°C │ 32°C │ 东北风│ 3 级  │ 59%  │
│ 温度  │ 体感  │ 风向  │ 风力  │ 湿度  │
└──────┴──────┴──────┴──────┴──────┘
```

核心技术：`parseWeatherItems()` 函数用正则 `/^(.+?)\s+(.+)$/` 把 `"温度 25°C"` 拆成 `{label:"温度", value:"25°C"}`。

### 4.2 室内环境面板（SensorPanel.tsx）

- 三个小卡片：温度(°C) / 湿度(%) / 光照(lux)
- 带缓冲区缓存（AsyncStorage 按日期分桶）
- 空状态："暂无传感器数据"
- AI 洞察显示区
- 刷新按钮（↻ 旋转动画）

### 4.3 数据加载逻辑（today.tsx）

```
loadSensorCached():
  1. 读 AsyncStorage 缓存（key: sensor_{userId}）
  2. 缓存命中且当天 → 直接渲染
  3. 缓存未命中 → fetchCurrentSensor() → 写缓存 + 渲染

handleRefreshSensor():
  1. 删缓存
  2. 并行调 fetchCurrentSensor() + fetchEnvironmentInsights()
  3. 写缓存
```

---

## 五、音频模块（实验性，未完成）

### 5.1 I2S 全双工环回

INMP441 麦克风 + MAX98357A 功放共用时钟线：

```
ESP32 GPIO5  ──┬── INMP441 SCK
               └── MAX98357A BCLK    (共用时钟)
ESP32 GPIO15 ──┬── INMP441 WS
               └── MAX98357A LRC     (共用帧同步)
ESP32 GPIO16 ──── INMP441 SD         (数据输入)
ESP32 GPIO8  ──── MAX98357A DIN      (数据输出)
```

I2S 配置：16kHz / 32-bit / 左声道 / 标准 I2S 格式 / 全双工模式。

### 5.2 AI 语音对话（未完成）

架构设计：
```
你说"樊玉明你好" → INMP441 → ESP32 录音 → HTTP POST → Python /voice/chat
                                                          │
                                              ┌───────────┴───────────┐
                                              │ Whisper STT (语音→文字) │
                                              │ DeepSeek LLM (思考回复) │
                                              │ edge-tts (文字→语音)    │
                                              └───────────┬───────────┘
                                                          │
你听到回复 ← MAX98357A ← ESP32 播放 ← WAV 音频 ←─────────┘
```

**未完成原因：** Windows 上 Whisper 依赖 ffmpeg 解码音频文件，numpy 直传可绕过但识别结果不稳定（返回空或乱码）。

---

## 六、文件清单

### 新建文件

| 文件 | 位置 | 作用 |
|------|------|------|
| `InfluxDBReader.java` | business-service/mqtt/ | 查 InfluxDB 最新传感器数据 |
| `InfluxDBWriter.java` | business-service/mqtt/ | 写传感器数据到 InfluxDB |
| `MqttSubscriber.java` | business-service/mqtt/ | 订阅 MQTT 主题，解析 JSON |
| `MqttConfig.java` | business-service/config/ | MQTT 客户端 Bean |
| `SensorController.java` | business-service/controller/ | GET /api/sensor/current |
| `SensorWebSocketHandler.java` | business-service/mqtt/ | WebSocket 广播传感器数据 |
| `WebSocketConfig.java` | business-service/config/ | WebSocket 端点配置 |
| `environment.py` | agent_service/routers/ | GET /environment/insights |
| `voice.py` | agent_service/routers/ | POST /voice/chat（实验） |
| `sensor_analysis.py` | agent_service/agents/ | LLM 环境分析 |
| `sensor_prompt.txt` | agent_service/prompts/ | LLM prompt 模板 |
| `influx_client.py` | agent_service/tools/ | Python InfluxDB 查询工具 |
| `sensor.ts` | dayagent-mobile/api/ | 传感器 API 封装 |
| `SensorPanel.tsx` | dayagent-mobile/components/ | 室内环境卡片 |
| `esp32-sensor-main.cpp` | docs/superpowers/specs/iot/ | ESP32 完整代码备份 |
| `esp32-platformio.ini` | docs/superpowers/specs/iot/ | PlatformIO 配置备份 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `docker-compose.yml` | Mosquitto 端口 `127.0.0.1:1883` → `1883:1883`（允许局域网） |
| `application.yml` | 新增 mqtt + influxdb 配置段 |
| `pom.xml` | 新增 MQTT(Paho) + InfluxDB + WebSocket 依赖 |
| `main.py` | 注册 environment + voice 路由 |
| `LifeController.java` | 新增 /environment/insights + /courses/ai-import 等 |
| `LifeAgentClient.java` | 新增 callEnvironmentInsights() 等多个方法 |
| `WeatherHero.tsx` | 一行文字 → 可视化卡片布局 |
| `today.tsx` | 集成 SensorPanel + 传感器数据加载 |

---

## 七、启动顺序

```
1. Docker Desktop 启动
2. docker compose up -d mosquitto influxdb mysql
3. Python: uvicorn agent_service.main:app --port 8000
4. Java: mvn spring-boot:run (在 business-service/)
5. 手机: npx expo start (在 dayagent-mobile/)
6. ESP32: 插 USB，串口监控看 WiFi OK + MQTT OK
```

---

## 八、验证全链路

```bash
# 1. 确认 Mosquitto 收到数据
docker exec dayagent-mosquitto mosquitto_sub -t "dayagent/+/sensor/environment" -C 1

# 2. 确认 API 返回真实数据
curl http://localhost:8080/api/sensor/current
# → {"temperature":25.6,"humidity":54.2,"co2":0,"light":37,"pm25":0}

# 3. 确认 AI 洞察
curl http://localhost:8080/api/environment/insights
# → {"current_readings":{...},"alerts":[...],"ai_insights":"..."}
```
