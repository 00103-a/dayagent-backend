"""
传感器数据模拟器 — MQTT 发布端
每 30 秒生成一组模拟传感器数据，发到 Mosquitto Broker。

启动：python agent_service/simulator/sensor_simulator.py
停止：Ctrl+C
"""
import json
import math
import random
import time
from datetime import datetime

import paho.mqtt.client as mqtt

# ── 配置 ──
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "dayagent/sim-01/sensor/environment"


class SensorState:
    """模拟房间内的环境状态"""
    def __init__(self):
        self.temperature = 25.0
        self.humidity = 60.0
        self.co2 = 500.0
        self.light = 400.0
        self.pm25 = 25.0
        self.window_open = False
        self.window_timer = 0


state = SensorState()


def tick():
    """每 30 秒走一步，更新所有传感器数值"""
    now = datetime.now()
    hour = now.hour + now.minute / 60.0

    # 温度：下午 2 点最高，凌晨 4 点最低（正弦波）
    state.temperature = round(
        26.0 + 3.5 * math.sin((hour - 8) * math.pi / 12) + random.uniform(-0.3, 0.3), 1
    )

    # 湿度：温度高 → 湿度低，成反比
    state.humidity = round(
        max(38, min(92, 75 - (state.temperature - 22) * 2 + random.uniform(-2, 2))), 1
    )

    # CO₂：缓慢上升（当作人在房间呼吸），开窗事件出现时骤降
    if state.window_open:
        state.window_timer -= 1
        state.co2 = max(400, state.co2 - random.uniform(20, 40))
        if state.window_timer <= 0:
            state.window_open = False
    else:
        state.co2 += random.uniform(3, 10)
        if random.random() < 0.008:  # 约每小时一次触发开窗
            state.window_open = True
            state.window_timer = random.randint(4, 10)
    state.co2 = round(min(2500, max(380, state.co2)))

    # 光照：白天亮晚上暗
    if 7 <= hour <= 18:
        state.light = round(300 + 500 * math.sin((hour - 7) * math.pi / 11) + random.uniform(-30, 30))
    else:
        state.light = round(max(10, random.uniform(10, 60)))

    # PM2.5：基准 + 随机波动
    state.pm25 = round(max(8, 25 + random.uniform(-10, 25)), 1)


def build_message():
    """把当前传感器数据打包成 JSON"""
    return json.dumps({
        "device_id": "sensor-sim-01",
        "timestamp": datetime.now().isoformat(),
        "temperature": state.temperature,
        "humidity": state.humidity,
        "co2": state.co2,
        "light": state.light,
        "pm25": state.pm25,
    })


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()
    print(f"[模拟器] 已连接, 开始发数据到 {TOPIC}（每30秒）")

    try:
        while True:
            tick()
            msg = build_message()
            client.publish(TOPIC, msg, qos=0)
            print(f"[模拟器] 已发送: temp={state.temperature}°C  "
                  f"hum={state.humidity}%  co2={state.co2}ppm  "
                  f"light={state.light}lux  pm25={state.pm25}")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[模拟器] 已停止")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
