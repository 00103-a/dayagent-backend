# DayAgent 桌面管家 — IoT 实体桌面伙伴设计文档（最终优化版）

> 日期：2026-06-02 | 最后更新：2026-06-03  
> 状态：架构已优化，可开发  
> 版本：v2.1 Final Optimized  
> 目标：打造"常驻桌面的 AI + IoT 智能生活管家"

---

# 1. 项目定位

DayAgent 不再只是一个"打开网页后才会使用"的工具，而是一个：

- 常驻后台，主动提醒
- 感知环境，理解用户状态
- 具有"人格感"的 AI 桌面管家

它是一个真实放在桌上的小设备，有屏幕、有传感器、会说话。

---

# 2. 三阶段演进路线

| 阶段 | 目标 | 成本 | 周期 |
|------|------|------|------|
| Phase 1：纯软件 IoT | 验证完整链路，零硬件 | 0 元 | 5 天 |
| Phase 2：真实传感器 | ESP32 + DHT22 + 真实数据 | 28 元 | +2 天 |
| Phase 3：实体桌面伙伴 | ESP32 + TFT 屏幕 + 外壳，形成完整实体 | 80 元 | +2 天 |

---

# 3. 核心体验设计

## 3.1 桌面常驻

- Electron 系统托盘常驻后台
- 开机自启动，用户无需主动打开
- 右键菜单快速访问功能

## 3.2 主动环境感知

系统实时获取：温度、湿度、CO₂、PM2.5、光照、天气、课程状态

AI 综合分析后主动提醒：
> "已经连续高 CO₂ 40 分钟了，建议开窗。"

## 3.3 AI 人格化体验

- 像素猫人格，Undertale/Sky 光遇风格
- 轻孤独感 + 温柔提醒
- 情绪化表达，有陪伴感

## 3.4 主动语音播报

- 早间播报（08:00）
- 晚间总结提醒（21:00）
- 环境异常提醒（实时）
- TTS 方案：Edge-TTS（免费，中文效果好）+ Piper（本地离线）

---

# 4. 技术架构

```
[Python 传感器模拟器 / ESP32]
            ↓ MQTT
    [Mosquitto Broker]
            ↓
  [Spring Boot + Paho]
            ↓
    ┌───────┴────────┐
    ↓                ↓
[InfluxDB]      [MySQL]
    ↓                ↓
  [快速查询]    [配置存储]
    ↓
  [FastAPI]
    ↓
LLM 分析（DeepSeek/Qwen）
    ↓
  [Vue 3 + Electron]
    ↓
  WebSocket 推送 → 实时 UI
  系统通知 + 语音播报
```

---

# 5. 传感器模拟器详细设计

### 5.1 模拟规则

**温度（18～32°C）**
- 基础：日周期正弦波（08:00 最低 20°C，14:00 最高 28°C）
- 噪声：±0.5°C 随机
- 特殊事件：上课时段+1°C（人多）、晚 22:00 后每小时-0.3°C、开窗-2°C

**湿度（40～85%）**
- 基础：与温度反相
- 特殊事件：下雨（概率 20%/4h）→ +10%，开窗→ -5%

**CO₂（400～1800 ppm）**
- 工作日 08:00(450) → 12:00(1200) → 14:00(800) → 22:00(550)
- 周末全天低值，开窗快速降

**光照（0～1000 lux）**
- 日周期：06:00(0) → 12:00(900) → 19:00(<50)
- 阴天（概率 10%/h）→ -30%

**PM2.5（10～150 μg/m³）**
- 白天低(20～50)，夜间高(40～80)
- 污染日（概率 2%/h）→ +40～60，开窗-15%

### 5.2 事件触发机制

所有特殊事件基于随机触发或时间规则，**支持 seed 模式**：
- 开发时：`SensorSimulator(seed=42)` → 可复现数据
- 生产时：`SensorSimulator()` → 真实随机

---

# 6. MQTT 消息设计

**Topic：** `dayagent/{device_id}/sensor/{sensor_type}`  
**消息示例：**
```json
{
  "device_id": "sim-01",
  "timestamp": "2026-06-02T10:30:00+08:00",
  "temperature": 26.3,
  "humidity": 68.5,
  "co2": 1240,
  "light": 520,
  "pm25": 35.2,
  "status": "online",
  "battery": 100
}
```

**QoS 策略：**
| 场景 | QoS |
|------|-----|
| 高频普通数据 | 0 |
| 关键告警 | 1 |
| 配置同步 | 2 |

---

# 7. 数据存储优化

## 7.1 InfluxDB

**存储：** 时序环境数据 + 高频采样

**保留策略：**
| 数据类型 | 保存时间 |
|---------|--------|
| 原始数据 | 7 天 |
| 聚合数据（1h avg） | 90 天 |
| AI 分析结果 | 长期 |

**避免高基数问题：** 使用 tag 存储设备 ID
```
✓ 好：measurement="temperature" tag="device_id=001" field="value"
✗ 差：measurement="sensors" field="temp_001", "temp_002"...
```

## 7.2 MySQL

用于：用户配置、设备信息、提醒规则、AI 个性设置

**不存储时序数据**（用 InfluxDB 替代）

---

# 8. API 端点设计

### REST API

| 端点 | 方法 | 说明 | 缓存 |
|------|------|------|------|
| `/api/sensors/latest` | GET | 最新传感器值 | 无 |
| `/api/sensors/history` | GET | 历史数据（1h/6h/24h） | 无 |
| `/api/sensors/{id}/status` | GET | 设备在线状态 | 无 |
| `/api/analysis/environment` | GET | AI 环境分析 | 10min |
| `/api/alerts/active` | GET | 活跃告警列表 | 无 |
| `/api/plan/today` | GET | 今日课程+天气+提醒 | 1h |

### WebSocket 实时推送

**端点：** `WS /api/sensors/realtime`

**推送策略：**
- **基础频率：** 30 秒推送一次最新值
- **告警加速：** CO₂/温度超标时立即推送（不等 30 秒）
- **心跳机制：** 60 秒发 ping，120 秒无响应则重连

**消息内容：**
```json
{
  "timestamp": "2026-06-02T10:30:00",
  "sensors": {
    "temperature": 26.3,
    "humidity": 68.5,
    "co2": 1240,
    "light": 520,
    "pm25": 35.2
  },
  "alerts": [
    { "type": "co2_high", "value": 1240, "threshold": 1000 }
  ]
}
```

---

# 9. AI 分析层

## 9.1 双层架构

### 第一层：规则引擎（无 LLM）

实时检测，极低延迟：
- CO₂ > 1200 ppm → "建议开窗"
- 温度 > 30°C → "注意降温"
- PM2.5 > 100 → "外出戴口罩"
- 光照 < 50 lux（晚间）→ "注意护眼"

### 第二层：LLM 深度分析

**频率：** 每 10 分钟一次

**输入：**
- 传感器聚合数据（最近 1h）
- 当日课程 + 天气
- 用户历史习惯

**输出：** 个性化建议
> "你下午有连续课程，但房间空气质量正在变差，建议现在休息并通风。"

## 9.2 LLM 成本估算

**使用 DeepSeek：**
```
分析频率：10 分钟/次
每次 Prompt：~500 token（传感器+日程+上下文）
每次生成：~200 token（建议）
每日分析：144 次
单价：输入 ¥0.0015/K，输出 ¥0.006/K

月成本 ≈ 4.5 元
```

**优化策略：**
1. 聚合数据减少 token → 节省 60%
2. 缓存结果（数据变化<5%）→ 节省 30～50%
3. 规则告警无需 LLM → 削减高频调用
4. 备选：Qwen（月 2 元）+ 本地 Ollama（离线免费）

---

# 10. Electron 开发调试工具

Electron 仅作为开发阶段的可视化调试界面，不是最终产品形态。最终显示层由 ESP32 + TFT 屏幕承担。

## 10.1 系统托盘

```
托盘菜单：
  ├─ 显示主窗口
  ├─ 今日播报
  ├─ 快速聊天
  ├─ 环境状态（温度/湿度/CO₂）
  └─ 退出
```

## 10.2 权限声明

**Windows：**
```json
{
  "build": {
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true
    }
  }
}
```
需要：麦克风、系统通知、文件系统

**macOS：**
```xml
<key>NSMicrophoneUsageDescription</key>
<string>DayAgent 需要麦克风权限以支持语音交互</string>

<key>NSLocalNetworkUsageDescription</key>
<string>DayAgent 需要本地网络权限以连接后端服务</string>
```

**Linux：** D-Bus 自动处理通知，需加入 audio 组

## 10.3 窗口状态管理

```
后台运行（托盘）
    ↓
[每 10 分钟] AI 分析完成
    ├─ 有重要结果 → 推送通知 → 用户点击 → 显示详情 → 关闭 → 回托盘
    └─ 无重要结果 → 静默更新
    
[定时事件]
    ├─ 08:00 → 早间播报窗口（3 秒自动关闭）
    └─ 21:00 → 晚间建议窗口
```

## 10.4 全局快捷键

建议：`Alt + Space` 快速唤醒 DayAgent

---

# 11. 前端 UI 方向

**推荐风格：**
- Liminal Space / Pixel Art
- Calm / Soft Glow
- Undertale / Sky 光遇
- 夜晚房间感

**避免：** 工业后台风、复杂表格、强商务化

**强化：** 情绪氛围、呼吸感动画、环境感 UI、AI 生物感

---

# 12. 安全与隐私

## 12.1 本地隐私原则

尽量：
- 本地推理（用 Ollama）
- 本地存储（MySQL + InfluxDB）
- 用户数据**不上传云端**

特别保护：
- 🎤 麦克风（离线 TTS 优先）
- 📊 环境数据（本地存储）
- 📅 用户日程（加密存储）

## 12.2 未来安全升级

- JWT 鉴权
- MQTT 用户认证
- TLS 加密
- API Rate Limit

---

# 13. 常见陷阱与解决方案

### ❌ 陷阱 1：InfluxDB 高基数问题

**问题：** 传感器数量 > 10 时写入性能严重下降

**解决：** 使用 tag 存储设备 ID，不用 field
```sql
✓ measurement="temperature" tag="device_id=001" field="value"
✗ measurement="sensors" field="temp_001", "temp_002"
```

### ❌ 陷阱 2：WebSocket 连接泄漏

**问题：** 窗口关闭但 WebSocket 还在重连，内存持续增长

**解决：**
```javascript
onBeforeUnmount(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.close(1000, 'Component unmounted');
  }
});
```

### ❌ 陷阱 3：LLM 调用阻塞 UI

**问题：** FastAPI 调用 LLM（网络 IO），UI 冻结 3～5 秒

**解决：** 使用异步队列
```python
async def analyze_sensors():
    task_id = await analysis_queue.put(sensor_data)
    return {"task_id": task_id, "status": "processing"}  # 立即返回
```

### ❌ 陷阱 4：Electron 托盘跨系统不兼容

**问题：** Windows/macOS/Linux 托盘显示完全不同

**解决：** 根据平台定制图标
```javascript
const iconPath = process.platform === 'darwin' 
  ? './assets/tray-icon-macos.png' 
  : './assets/tray-icon-win.ico';
```

### ❌ 陷阱 5：模拟器数据不可复现

**问题：** 随机事件难以调试，特殊场景验证困难

**解决：** 支持 seed 模式
```python
# 开发时可复现
sim = SensorSimulator(seed=42)
# 生产时真实随机
sim = SensorSimulator()
```

### ❌ 陷阱 6：MQTT 消息丢失

**问题：** Mosquitto 重启，缓冲区消息丢失

**解决：** Docker 配置持久化
```yaml
mosquitto:
  volumes:
    - mosquitto_data:/mosquitto/data  # 持久化消息队列
```

### ❌ 陷阱 7：时区混乱

**问题：** Python 生成 UTC 时间，前端显示时晚 8 小时

**解决：** 统一使用带时区信息的 ISO 格式
```python
from datetime import datetime
import pytz
tz = pytz.timezone('Asia/Shanghai')
now = datetime.now(tz)
timestamp = now.isoformat()  # 包含 +08:00
```

### ❌ 陷阱 8：没有监控和日志

**问题：** 后台运行一周，某个组件崩溃，用户无感知

**解决：** 添加健康检查端点
```python
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "mqtt": await check_mqtt(),
        "influxdb": await check_influxdb(),
        "llm": await check_llm()
    }
```

### ❌ 陷阱 9：没有备份策略

**问题：** InfluxDB 数据库损坏，数据全丢

**解决：** 定时备份
```bash
0 2 * * * influxd backup /backup/influx-$(date +%Y%m%d)
0 3 * * * mysqldump -u root all_databases > /backup/mysql-$(date +%Y%m%d).sql
```

---

# 14. 降级策略

| 故障 | 降级方案 |
|------|--------|
| MQTT 挂掉 | 自动重连 + 缓存队列 |
| InfluxDB 挂掉 | 临时写 MySQL |
| LLM 失败 | 仅规则告警 |
| Electron 崩溃 | 后端继续运行 |
| 模拟器停止 | 标记数据过期 |
| Docker 未启动 | 自动检测并警告 |

---

# 15. 性能指标与资源评估

## 15.1 数据量

| 项目 | 数值 |
|------|------|
| 日均 MQTT 消息 | 2,880 条（30s 一次） |
| 日均 InfluxDB 写入 | ~14.4K points |
| 月存储量 | ~500 MB |
| 日均 LLM 调用 | 144 次（10min 一次） |

## 15.2 进程内存占用

| 进程 | 内存 | CPU | 备注 |
|-----|------|-----|------|
| Electron 客户端 | ~300 MB | <1% | 空闲 |
| Spring Boot | ~400 MB | 1～3% | MQTT + WebSocket |
| FastAPI | ~200 MB | <1% | LLM 调用时峰值 20% |
| Python 模拟器 | ~50 MB | <0.5% | 持续 |
| **总计** | **~1.3 GB** | **5～10%** | 正常运行 |

## 15.3 Docker 资源限制（建议）

```yaml
mysql:
  mem_limit: 512m
  cpus: '0.5'

influxdb:
  mem_limit: 512m
  cpus: '1.0'

mosquitto:
  mem_limit: 128m
  cpus: '0.3'
```

---

# 16. 实施计划

## 16.1 标准版本（5 天）

### Day 1：MQTT 数据接入

**任务：**
1. Docker Compose 启动 Mosquitto + InfluxDB + MySQL
2. Spring Boot Paho MQTT 订阅
3. 数据写入 InfluxDB

**验收：** InfluxDB 有可查询的数据点

---

### Day 2：模拟器 + 数据聚合

**任务：**
1. Python 模拟器，30 秒发一次 MQTT
2. Spring Boot REST API：`GET /api/sensors/latest`
3. InfluxDB 数据可查询验证

**验收：** 模拟器连续运行 5 分钟，API 返回最新值

---

### Day 3：前端可视化 + WebSocket

**任务：**
1. Vue 组件：`SensorCard.vue` + `SensorChart.vue`
2. Spring Boot WebSocket `/api/sensors/realtime`
3. ECharts 趋势图（1h/6h/24h）

**验收：** 浏览器看到 5 个卡片 + 动态折线图

---

### Day 4：AI 分析 + 规则告警

**任务：**
1. FastAPI `/api/analysis/environment`（调用 LLM）
2. Spring Boot 规则引擎（CO₂/温度告警）
3. Vue"AI 环境洞察"卡片
4. 系统通知

**验收：** 修改传感器值，看到告警推送和 AI 建议

---

### Day 5：Electron 桌面端 + 全链路

**任务：**
1. Electron 构建 + 系统托盘
2. 定时播报（08:00 早，21:00 晚）
3. 全链路测试 2～3 小时

**验收：** 应用可打包，托盘可用，无内存泄漏

---

## 16.2 快速 MVP 版本（2 天）

如果只有周末 8 小时：

### 范围
```
✓ Docker + 模拟器 → MQTT → InfluxDB
✓ Spring Boot 接收 + REST API
✓ 简单 Vue 页面
✗ WebSocket（用 HTTP 轮询）
✗ ECharts（用数字显示）
✗ LLM 分析（用规则告警）
✗ Electron（用浏览器）
```

### 时间分配
- **Day 1(4h)：** Docker(0.5h) + 模拟器(1.5h) + REST API(2h)
- **Day 2(4h)：** Vue 页面+轮询(2h) + 规则告警(1h) + 测试(1h)

**验收：** 打开 `http://localhost:3000` 能看到实时传感器数据 ✅

**然后迭代：** 加 WebSocket、ECharts、AI、Electron

---

# 17. 后续可扩展方向

- **AI 情绪系统**：根据天气、时间、环境改变 UI 和文案
- **多 Agent 协作**：学习、健康、环境、日程 Agent 联动
- **本地模型支持**：Ollama/Qwen/DeepSeek 离线推理
- **物理副屏**：旧手机/树莓派 常驻显示 DayAgent 状态

---

# 18. 项目价值

这个项目已经超越"课程提醒软件"，成为：

> **"具有环境感知、主动提醒、人格化交互能力的桌面 AI Agent 系统"**

覆盖领域：
- ✅ AI Agent（LLM 分析、上下文理解）
- ✅ IoT（传感器、MQTT、实时数据采集）
- ✅ 桌面应用（Electron、系统集成）
- ✅ 实时系统（WebSocket、WebWorker）
- ✅ 时序数据库（InfluxDB、数据建模）
- ✅ 完整后端（Spring Boot、FastAPI、微服务）
- ✅ 前端工程（Vue 3、组件化、性能优化）

**这是完整的全栈系统设计能力。**

---

# 19. 简历描述

> 独立设计并实现桌面 AI Agent 系统 DayAgent，融合 IoT 环境感知、LLM 分析与 Electron 桌面常驻体验。系统基于 MQTT + Spring Boot + InfluxDB 构建实时数据链路，通过 FastAPI 集成 DeepSeek/Qwen 进行环境分析与个性化建议生成。前端采用 Vue 3 + Electron 实现实时可视化、系统托盘、定时播报与 AI 对话，支持后续 ESP32 真实硬件扩展。

---

# 20. 最终目标

最终的 DayAgent：

不是一个网页。

不是一个 AI 聊天框。

而是：

> **"真正住在桌面里的 AI 伙伴。"**

它会在你需要的时刻主动出现，理解你的环境，给出智慧的建议。

不打扰，但总在。

它不在屏幕里，它就在你桌上。一个真实的、有重量的、会呼吸的小东西。

---

**下一步？** 选择 MVP（2 天）还是标准版（5 天），立即开始编码。

