package com.dayagent.controller;

import java.util.HashMap;
import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import com.dayagent.mqtt.InfluxDBReader;

import lombok.RequiredArgsConstructor;

@RestController
@RequiredArgsConstructor
public class SensorController {

    private final InfluxDBReader reader;

    @GetMapping("/api/sensor/current")
    public Map<String, Object> current() {
        // 从 InfluxDB 查最新一条真实数据
        Map<String, Object> data = reader.queryLatest();
        if (data != null) {
            return data; // 返回真实传感器数据
        }
        // 降级：InfluxDB 没有数据时，返回 null 值
        // 前端 SensorPanel 会显示"暂无传感器数据"
        Map<String, Object> fallback = new HashMap<>();
        fallback.put("temperature", null);
        fallback.put("humidity", null);
        fallback.put("co2", null);
        fallback.put("light", null);
        fallback.put("pm25", null);
        return fallback;
    }
}
