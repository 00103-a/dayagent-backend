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

## 九、代码逐行讲解（萌新友好版）

> 本节能让你读懂每个文件在干什么。适合刚学编程、只看过 Python/JS 基础语法的读者。

### 9.1 编程语言速查

| 文件后缀 | 语言 | 类比 | 特点 |
|---------|------|------|------|
| `.cpp` | C++ | 比 Python 啰嗦但能直接管硬件 | 需要手动管内存 |
| `.java` | Java | Spring Boot 自动帮你管 | 注解很多（`@` 开头的） |
| `.py` | Python | 你熟悉的 | 简洁 |
| `.tsx` / `.ts` | TypeScript | JavaScript + 类型检查 | React 组件 |

### 9.2 基本概念：三个编程通用术语

| 术语 | 意思 | 类比 |
|------|------|------|
| **变量** | 一个贴了标签的盒子，存数据 | `int age = 18;` → 标签叫 age，盒子里面是 18 |
| **函数** | 一段有名字的代码，呼叫它就执行 | `readTemperature()` → 呼叫它 → 它去读传感器 → 返回一个数字给你 |
| **类型** | 约定盒子里放什么 | `int` = 整数，`float` = 小数，`String` = 文字 |

---

### 9.3 ESP32 代码（C++）：`main.cpp`

**完整文件结构：**

```cpp
// ========== 第1块：引入工具库（类似 Python 的 import） ==========
#include <WiFi.h>          // WiFi 库：连无线的
#include <PubSubClient.h>  // MQTT 库：发消息的
#include <DHT.h>           // DHT 传感器库：读温湿度的
#include <Wire.h>          // I2C 通信库：和 BH1750 说话用

// ========== 第2块：定义常量（给引脚起名字） ==========
#define DHTPIN 4           // #define = 取别名。"4号脚"以后叫"DHTPIN"

// ========== 第3块：创建对象（"请来一个XXX助手"） ==========
DHT dht(DHTPIN, DHT22);    // 创建一个 DHT 助手，告诉他"4号脚，DHT22型号"
WiFiClient wifiClient;     // 创建一个 WiFi 助手
PubSubClient mqtt(wifiClient); // 创建一个 MQTT 助手，告诉它用 WiFi 发消息
```

**逐行讲解 `setup()` 函数 —— 开机只跑一次：**

```cpp
void setup() {
    // ---------- 引脚模式设置 ----------
    // pinMode(脚号, 模式) = 告诉芯片"这只脚是输出还是输入"
    pinMode(TFT_BL, OUTPUT);   // 背光脚 = 输出（我要控制它亮暗）
    digitalWrite(TFT_BL, LOW); // 先把背光关了（LOW=0V，HIGH=3.3V）

    // ---------- 屏幕硬件复位 ----------
    // 就像你电脑死机了长按电源键重启
    pinMode(TFT_RST, OUTPUT);
    digitalWrite(TFT_RST, HIGH);  // 常态：高电平
    delay(10);                    // 等10毫秒（千分之一秒）
    digitalWrite(TFT_RST, LOW);   // 按下去：低电平
    delay(10);                    // 按住10毫秒
    digitalWrite(TFT_RST, HIGH);  // 松手：恢复高电平
    delay(120);                   // 等120毫秒让芯片加载完
    digitalWrite(TFT_BL, HIGH);   // 开背光

    // ---------- SPI 通信初始化 ----------
    // SPI = 屏幕和芯片之间的"高速对话通道"
    // begin(时钟脚, 不用, 数据脚, 片选脚)
    // -1 = MISO 脚不需要（屏幕只收不发）
    SPI.begin(TFT_SCK, -1, TFT_MOSI, TFT_CS);

    // ---------- 屏幕初始化 ----------
    // init(宽240, 高320, 通信模式0)
    tft.init(240, 320, SPI_MODE0);
    tft.setSPISpeed(4000000);     // 通信速度：每秒400万次（杜邦线太长要降速）
    tft.invertDisplay(false);    // 不反转颜色
    tft.setRotation(0);          // 屏幕方向：0=竖屏
    tft.fillScreen(ST77XX_BLACK); // 全屏涂黑

    // ---------- 传感器启动 ----------
    dht.begin();        // DHT22：醒醒
    bh1750_begin();     // BH1750：你也醒醒

    // ---------- WiFi 连接 ----------
    WiFi.begin("菠萝手机", "12345678");  // 连接热点
    // 等30秒，连不上就算了
    while (WiFi.status() != WL_CONNECTED && retry < 30) {
        delay(1000);  // 每秒重试一次
        retry++;
    }

    // ---------- MQTT 连接 ----------
    mqtt.setServer("10.130.249.183", 1883); // 告诉它"消息中转站"的地址
    mqtt.connect("esp32-s3");                // 用设备名"esp32-s3"登入
}
```

**逐行讲解 `loop()` 函数 —— 无限循环，相当于心跳：**

```cpp
void loop() {
    // ===== 第一步：读传感器 =====
    float temp  = dht.readTemperature();  // 读温度（浮点数=带小数点的数）
    float hum   = dht.readHumidity();     // 读湿度
    float light = bh1750_read();          // 读光照

    // ===== 第二步：屏幕显示 =====
    // fillRect(x, y, 宽度, 高度, 颜色) = 画一个实心矩形
    tft.fillRect(0, 60, 240, 260, ST77XX_BLACK); // 先擦掉旧数据

    // setCursor(x, y) = 把"笔"移到(x,y)位置，准备写字
    // print(变量, 小数点位数) = 在当前位置写字
    tft.setCursor(10, 70);
    tft.print("Temp: ");
    tft.print(temp, 1);   // 1 = 保留1位小数，如 26.3
    tft.print(" C");

    // ===== 第三步：拼 JSON 发 MQTT =====
    // String = C++ 里的字符串类型
    String json = "{\"device_id\":\"esp32-s3\"";
    json += ",\"temperature\":" + String(temp, 1);   // 拼接温度
    json += ",\"humidity\":" + String(hum, 1);       // 拼接湿度
    json += ",\"co2\":0";                             // CO2 传感器没接，填0
    json += ",\"light\":" + String(light, 0);        // 拼接光照
    json += ",\"pm25\":0";                            // PM2.5 没接，填0
    json += "}";

    // ===== 第四步：发送 =====
    // publish("主题名", "消息内容")
    mqtt.publish("dayagent/esp32-s3/sensor/environment", json.c_str());

    delay(2000);  // 歇2秒再循环
}
```

---

### 9.4 BH1750 光照传感器（C++）：手写驱动

```cpp
void bh1750_begin() {
    Wire.begin(7, 6);                // 1️⃣ 开启 I2C 通信：SDA=7脚, SCL=6脚

    Wire.beginTransmission(0x23);    // 2️⃣ 开始跟 0x23 设备说话
    //     ↑ I2C 每条总线上可以挂多个设备，每个有唯一编号（地址）
    //     0x23 = BH1750 出厂地址（十六进制，等于十进制的35）

    Wire.write(0x10);                // 3️⃣ 发送命令：连续高分辨率模式
    //     0x10 = 告诉 BH1750 "开始持续测量，精度1勒克斯"

    Wire.endTransmission();          // 4️⃣ 说完
}

float bh1750_read() {
    Wire.requestFrom(0x23, 2);       // 1️⃣ 向 BH1750 要 2 字节数据

    uint16_t raw = Wire.read() << 8; // 2️⃣ 读第1字节（高8位），左移8位
    //     << 8 = 左移运算符，相当于 "后面补8个0"
    //     如果读到的第1字节是 0x01 (二进制 00000001)
    //     左移8位后变成 00000001 00000000 = 256

    raw |= Wire.read();              // 3️⃣ 读第2字节（低8位），按位或合并
    //     |= 是"按位或+赋值"，把第2字节塞进 raw 的低8位

    return raw / 1.2;                // 4️⃣ 芯片规定：原始值÷1.2 = 勒克斯
}
```

---

### 9.5 Java 代码：`MqttSubscriber.java`

**Java 文件结构：**

```java
package com.dayagent.mqtt;       // 声明这个文件属于哪个包（类似文件夹路径）

import org.springframework.stereotype.Component;  // 引入 Spring 工具

@Component                         // 告诉 Spring："帮我管理这个类"
public class MqttSubscriber {      // 定义一个叫 MqttSubscriber 的类
    // 类的内部：变量 + 函数（在 Java 里叫"方法"）
}
```

**依赖注入 —— Java 最核心的概念：**

```java
// @Component = 把这个类标记为"公共设施"
// 构造函数 = Spring 自动帮你把 MqttClient 和 InfluxDBWriter 传进来
// 你不需要 new，框架帮你 new

private final MqttClient client;      // MQTT 客户端（发消息用的）
private final InfluxDBWriter writer;  // 数据库写入器

public MqttSubscriber(MqttClient client, InfluxDBWriter writer) {
    this.client = client;   // "this.client" 指自己的变量，"client" 指传进来的参数
    this.writer = writer;
}
```

**MQTT 订阅 —— 收到消息后干啥：**

```java
@PostConstruct                    // 这行代码在对象创建后立刻自动执行
public void subscribe() throws MqttException {
    client.subscribe("dayagent/+/sensor/environment", (topic, message) -> {
        // ↑ "订阅"就是告诉 MQTT 中转站：
        // "所有 dayagent/XX/sensor/environment 主题的消息我都要"
        // + 是通配符，意思是"任意设备名"

        String json = new String(message.getPayload());  // 字节变字符串
        saveToInfluxDB(json);  // 存进数据库
    });
}

private void saveToInfluxDB(String json) {
    Map<String, Object> d = mapper.readValue(json, Map.class);
    // ↑ JSON 字符串 → Java 的 Map（相当于 Python 的字典）

    // 从 Map 里取各个字段，如果没有那字段就用 0.0
    double temp = toDouble(d, "temperature");
    double hum  = toDouble(d, "humidity");
    double co2  = toDouble(d, "co2");
    double lux  = toDouble(d, "light");
    double pm25 = toDouble(d, "pm25");

    writer.save("esp32-s3", temp, hum, co2, lux, pm25);
    // ↑ 调用写入器，存进 InfluxDB
}
```

---

### 9.6 Java 代码：`SensorController.java`

**接口（API）的写法：**

```java
@RestController                    // 标记："我是一个 HTTP 接口类"
@RequiredArgsConstructor           // 自动生成构造函数（Lombok 注解）
public class SensorController {

    private final InfluxDBReader reader;  // 数据库查询器

    @GetMapping("/api/sensor/current")   // 标记：GET 请求走这里
    public Map<String, Object> current() {
        Map<String, Object> data = reader.queryLatest();  // 查数据库
        if (data != null) {
            return data;   // 有数据就返回
        }
        // 没数据：返回全 null，手机端显示"暂无数据"
        Map<String, Object> fallback = new HashMap<>();
        fallback.put("temperature", null);
        fallback.put("humidity", null);
        fallback.put("co2", null);
        fallback.put("light", null);
        fallback.put("pm25", null);
        return fallback;
    }
}
```

**关键注解：**
| 注解 | 作用 |
|------|------|
| `@RestController` | 这个类处理 HTTP 请求 |
| `@GetMapping("/路径")` | 收到 GET /路径 就执行下面这个方法 |
| `@RequiredArgsConstructor` | Lombok 帮你自动写构造函数 |
| `@Component` | Spring 自动管理这个类的对象 |

---

### 9.7 Java 代码：`InfluxDBWriter.java`（数据库写入）

```java
@Component
public class InfluxDBWriter {

    // @Value = 从配置文件（application.yml）读值
    @Value("${influxdb.url}")
    private String url;              // http://localhost:8086

    @Value("${influxdb.token}")
    private String token;            // 密钥（相当于密码）

    @Value("${influxdb.org}")
    private String org;              // 组织名：dayagent

    @Value("${influxdb.bucket}")
    private String bucket;           // 桶名：sensors（相当于 MySQL 的表）

    private InfluxDBClient client;   // 数据库连接

    @PostConstruct                   // 对象创建后立刻执行：连数据库
    public void init() {
        this.client = InfluxDBClientFactory.create(url, token, org, bucket);
    }

    public void save(String deviceId, double temperature, double humidity,
                     double co2, double light, double pm25) {
        // Point = InfluxDB 的"一行数据"
        Point point = Point.measurement("sensor_readings")  // 表名
                .addTag("device_id", deviceId)              // 标签：哪个设备
                .addField("temperature", temperature)       // 字段：温度值
                .addField("humidity", humidity)
                .addField("co2", co2)
                .addField("light", light)
                .addField("pm25", pm25)
                .time(Instant.now(), WritePrecision.NS);   // 时间戳

        client.getWriteApiBlocking().writePoint(point);     // 真的写入
    }
}
```

**InfluxDB 数据存储结构：**

```
数据库 → Bucket(sensors) → Measurement(sensor_readings)
                                    │
                                    ├── 时间戳: 2026-06-07 19:30:00
                                    ├── 标签: device_id=esp32-s3
                                    ├── 字段: temperature=25.6
                                    ├── 字段: humidity=54.2
                                    └── 字段: light=37.0
```

---

### 9.8 Java 代码：`InfluxDBReader.java`（数据库读取）

```java
public Map<String, Object> queryLatest() {
    // Flux 是 InfluxDB 的查询语言（类似 SQL 但更像流水线）
    String flux = """
        from(bucket: "sensors")                     // 从 sensors 桶里拿
            |> range(start: -5m)                    // 只要最近5分钟的
            |> filter(fn: (r) => r._measurement == "sensor_readings")  // 只看传感器读数这张表
            |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value") // 宽表转换
            |> sort(columns: ["_time"], desc: true) // 按时间倒序（最新在前）
            |> limit(n: 1)                          // 只要1条
        """;

    List<FluxTable> tables = client.getQueryApi().query(flux);

    // 遍历结果，取出 temperature, humidity, co2, light, pm25
    for (FluxTable table : tables) {
        for (FluxRecord record : table.getRecords()) {
            Map<String, Object> row = new LinkedHashMap<>();
            for (String field : new String[]{"temperature","humidity","co2","light","pm25"}) {
                row.put(field, record.getValueByKey(field));
            }
            return row;  // 找到第一条就返回
        }
    }
    return null;  // 没数据
}
```

**Flux 查询语言对比 SQL：**

| 要做的事 | SQL | Flux |
|---------|-----|------|
| 指定查哪张表 | `FROM sensor_readings` | `from(bucket:"sensors") \|> filter(r._measurement=="sensor_readings")` |
| 条件筛选 | `WHERE time > NOW()-5m` | `\|> range(start: -5m)` |
| 排序 | `ORDER BY time DESC` | `\|> sort(desc: true)` |
| 只取几条 | `LIMIT 1` | `\|> limit(n: 1)` |

---

### 9.9 Python 代码：`environment.py`（AI 环境洞察）

```python
from fastapi import APIRouter, Query    # FastAPI 框架

router = APIRouter(prefix="/environment", tags=["环境"])

@router.get("/insights")
async def get_environment_insights(user_id: str = Query("1")):
    # 1. 查最新一条数据
    latest = query_latest()

    # 2. 查最近60分钟所有数据（看趋势）
    recent = query_recent(minutes=60)

    # 3. 调 AI 分析
    ai_insights = await analyze_environment(recent)

    # 4. 规则告警（不依赖 AI，立刻出结果）
    alerts = _check_alerts(latest)

    return {
        "current_readings": latest,   # 最新数值
        "alerts": alerts,             # 告警列表
        "ai_insights": ai_insights,   # AI 分析文字
    }
```

**告警规则 —— 纯逻辑，不调 AI：**

```python
def _check_alerts(latest: dict) -> list[dict]:
    alerts = []
    if latest.get("co2", 0) > 1500:
        alerts.append({"type": "co2_high", "message": "CO2偏高，建议开窗通风"})
    if latest.get("temperature", 0) > 30:
        alerts.append({"type": "temp_high", "message": "温度偏高，注意防暑"})
    if latest.get("humidity", 0) > 85:
        alerts.append({"type": "hum_high", "message": "湿度较高，感觉闷热"})
    if latest.get("pm25", 0) > 75:
        alerts.append({"type": "pm25_high", "message": "PM2.5偏高，减少开窗"})
    return alerts
```

---

### 9.10 Python 代码：`influx_client.py`（数据库查询）

```python
from influxdb_client import InfluxDBClient

# 连接信息（优先读环境变量，读不到用默认值）
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "dayagent-dev-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "dayagent")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "sensors")

_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)

def query_latest() -> dict | None:
    """查最新一条传感器数据"""
    flux = f"""
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -5m)
        |> filter(fn: (r) => r._measurement == "sensor_readings")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: 1)
    """
    result = _client.query_api().query(flux)
    # 遍历结果，提取 temperature/humidity/co2/light/pm25
    for table in result:
        for record in table.records:
            return {
                "time": record.get_time().isoformat(),
                "temperature": record.values.get("temperature"),
                "humidity": record.values.get("humidity"),
                "co2": record.values.get("co2"),
                "light": record.values.get("light"),
                "pm25": record.values.get("pm25"),
            }
    return None  # 没数据
```

---

### 9.11 TypeScript 代码：`api/sensor.ts`（移动端 API）

```typescript
import { apiClient } from './client';  // 引入封装好的 axios 实例

// ① interface = 定义数据长什么样
// TypeScript 独有：写错了字段名编辑器直接标红
export interface SensorCurrent {
    temperature: number;   // number = 数字类型
    humidity: number;
    co2: number;
    light: number;
    pm25: number;
}

// ② async function = 异步函数
// 调用后端需要时间，用 async/await 等它返回
// Promise<T> = "我承诺给你一个 T 类型的数据，但要等一下"
export async function fetchCurrentSensor(): Promise<SensorCurrent> {
    const res = await apiClient.get('/api/sensor/current');
    // res.data = 后端返回的 JSON
    // res.data.data = Spring Boot 统一包装后的真实数据
    // ?? = "如果左边是 null/undefined，用右边的"
    return (res.data?.data ?? res.data) as SensorCurrent;
}
```

---

### 9.12 TypeScript 代码：`WeatherHero.tsx`（天气改造）

**parseWeatherItems —— 把一行字拆成结构化数据：**

```typescript
// 输入："南昌今日天气：阴，温度 31°C，体感温度 32°C，北风 2 级，相对湿度 65%"
// 输出：[{label:"阴",value:""}, {label:"温度",value:"31°C"}, ...]

function parseWeatherItems(temp: string): { label: string; value: string }[] {
    // 1. 找中文冒号，切掉前缀 "南昌今日天气："
    const colonIdx = temp.indexOf('：');     // indexOf = 找中文冒号位置
    const body = colonIdx !== -1             // !== -1 = "找到了"
        ? temp.slice(colonIdx + 1)           // 切掉前缀
        : temp;                              // 没找到就原样

    // 2. 按中文逗号切碎
    const parts = body.split('，').filter(Boolean);
    // filter(Boolean) = 去掉空字符串

    // 3. 遍历每个碎片，用正则拆分
    const items: { label: string; value: string }[] = [];
    for (const p of parts) {
        // /^(.+?)\s+(.+)$/ = 找到"空格"并在那里切开
        // "温度 31°C" → match[1]="温度"  match[2]="31°C"
        const match = p.match(/^(.+?)\s+(.+)$/);
        if (match) {
            items.push({ label: match[1], value: match[2] });
        } else {
            items.push({ label: p, value: '' }); // 没空格的（如"阴"）
        }
    }
    return items;
}
```

**React 组件三段式：**

```tsx
// ===== 第一段：import（拿工具） =====
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../constants/theme';

// ===== 第二段：组件函数（逻辑 + 渲染） =====
export default function WeatherHero({ location, weatherItems }) {
    return (
        // JSX = 在 JavaScript 里写 HTML
        // { } = 插入 JS 变量（相当于 Vue 的 {{ }}）
        <View style={styles.container}>
            <Text style={styles.date}>{location}</Text>

            {weatherItems.map((item, i) => (
                // .map() = 遍历数组，每个元素渲染一个小卡片
                <View key={i} style={styles.miniCard}>
                    <Text style={styles.miniValue}>{item.value}</Text>
                    <Text style={styles.miniLabel}>{item.label}</Text>
                </View>
            ))}
        </View>
    );
}

// ===== 第三段：样式（相当于 CSS） =====
const styles = StyleSheet.create({
    container: { paddingHorizontal: 16 },
    date: { color: '#d4c5b2', fontSize: 9 },
    miniCard: { flex: 1, backgroundColor: 'rgba(224,112,48,0.08)' },
    miniValue: { color: '#d4c5b2', fontSize: 13 },
    miniLabel: { color: '#8a7a65', fontSize: 9 },
});
```

---

### 9.13 TypeScript 代码：`SensorPanel.tsx`（室内环境卡片）

**数据类型驱动渲染：**

```tsx
// 定义三个指标 —— 数据驱动，不是硬编码三遍
const METRICS = [
    { key: 'temperature', label: '温度', unit: '°C' },
    { key: 'humidity',    label: '湿度', unit: '%'  },
    { key: 'light',       label: '光照', unit: ' lux' },
];

// 条件渲染：有数据画卡片，没数据显示空状态
{data ? (
    <View style={styles.cardRow}>
        {METRICS.map(m => {
            const displayValue =
                typeof data[m.key] === 'number'
                    ? `${data[m.key]}${m.unit}`   // 有值："26.3°C"
                    : '--';                        // 没值：显示"--"
            return (
                <View key={m.key} style={styles.miniCard}>
                    <Text>{displayValue}</Text>
                    <Text>{m.label}</Text>
                </View>
            );
        })}
    </View>
) : (
    <Text>暂无传感器数据</Text>   // 空状态
)}
```

**React 三个核心概念对照：**

| Vue | React Native | 说明 |
|-----|-------------|------|
| `ref()` | `useState(初始值)` | 变量变化时界面自动刷新 |
| `{{ }}` | `{ }` | 在 JSX 里插入 JS 表达式 |
| `@click` | `onPress` | 点击事件 |

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
