package com.dayagent.mqtt;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;

import java.util.Map;

import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * MQTT 消息订阅器
 * 订阅传感器 Topic，收到消息后打印日志
 * TODO: 后续解析 JSON 并写入 InfluxDB
 */
@Component
@ConditionalOnProperty(prefix = "mqtt", name = "enabled", havingValue = "true")
public class MqttSubscriber {

    private static final Logger log = LoggerFactory.getLogger(MqttSubscriber.class);

    private final MqttClient client;
    
    private final InfluxDBWriter writer;

    private final SensorWebSocketHandler wsHandler;

    private final ObjectMapper mapper = new ObjectMapper();


    @Value("${mqtt.topics}")
    private String topicFilter;

    public MqttSubscriber(MqttClient client, InfluxDBWriter writer,
                          SensorWebSocketHandler wsHandler) {
        this.client = client;
        this.writer = writer;
        this.wsHandler = wsHandler;
    }

    @PostConstruct
    public void subscribe() throws MqttException {
        client.subscribe(topicFilter, (topic, message) -> {
            String json = new String(message.getPayload());
            log.info("[MQTT] 收到消息 topic={} ", topic);
            saveToInfluxDB(json);
        });
        log.info("[MQTT] 已订阅 Topic: {}  (连接状态: {})",
                topicFilter, client.isConnected() ? "已连接" : "未连接");
    }
    
    private void saveToInfluxDB(String json){
      try {
        Map<String, Object> d = mapper.readValue(json, Map.class);
        String id   = (String) d.get("device_id");
        double temp = toDouble(d, "temperature");
        double hum  = toDouble(d, "humidity");
        double co2  = toDouble(d, "co2");
        double lux  = toDouble(d, "light");
        double pm25 = toDouble(d, "pm25");
        writer.save(id, temp, hum, co2, lux, pm25);
        log.info("[MQTT] → InfluxDB 写入成功: temp={}℃, hum={}%", temp, hum);
        wsHandler.broadcast(json);  // WebSocket 实时推送给前端
          } catch (Exception e) {
              log.error("[MQTT] 写入失败: {} — json={}", e.getMessage(), json);
          }
      }

    private double toDouble(Map<String, Object> m, String key) {
        Object v = m.get(key);
          return v instanceof Number ? ((Number) v).doubleValue() : 0.0;
      }
    
    @PreDestroy
    public void cleanup() {
        try {
            if (client.isConnected()) {
                client.disconnect();
                log.info("[MQTT] 已断开连接");
            }
        } catch (MqttException e) {
            log.warn("[MQTT] 断开异常: {}", e.getMessage());
        }
    }
}
