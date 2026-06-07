package com.dayagent.mqtt;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.InfluxDBClientFactory;
import com.influxdb.client.InfluxDBClientOptions;
import com.influxdb.client.WriteApiBlocking;
import com.influxdb.client.domain.WritePrecision;
import com.influxdb.client.write.Point;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.Instant;

/**
 * InfluxDB 写入器
 * 把传感器数据存进 InfluxDB 时序数据库
 */
@Component
public class InfluxDBWriter {

    private static final Logger log = LoggerFactory.getLogger(InfluxDBWriter.class);

    /* ── 连接信息（从 application.yml 读取）── */
    @Value("${influxdb.url}")
    private String url;           // InfluxDB 地址，默认 http://localhost:8086

    @Value("${influxdb.token}")
    private String token;         // 密钥，docker-compose 里设的 dayagent-dev-token

    @Value("${influxdb.org}")
    private String org;           // 组织名 dayagent

    @Value("${influxdb.bucket}")
    private String bucket;        // 桶名 sensors，相当于 MySQL 的表

    private InfluxDBClient client; // 和 InfluxDB 之间的连接

    /* ── 启动时自动连接 ── */
    @PostConstruct
    public void init() {
        InfluxDBClientOptions options = InfluxDBClientOptions.builder()
                .url(url)
                .authenticateToken(token.toCharArray())
                .org(org)
                .bucket(bucket)
                .build();
        this.client = InfluxDBClientFactory.create(options);
        log.info("[InfluxDB] 已连接 {} (bucket={})", url, bucket);
    }

    /* ── 存一条传感器数据 ── */
    public void save(String deviceId, double temperature, double humidity,
                     double co2, double light, double pm25) {
        Point point = Point.measurement("sensor_readings")
                .addTag("device_id", deviceId)
                .addField("temperature", temperature)
                .addField("humidity", humidity)
                .addField("co2", co2)
                .addField("light", light)
                .addField("pm25", pm25)
                .time(Instant.now(), WritePrecision.NS);

        WriteApiBlocking writeApi = client.getWriteApiBlocking();
        writeApi.writePoint(point);
        log.info("[InfluxDB] 已写入: device={}, temp={}°C, hum={}%", deviceId, temperature, humidity);
    }

    /* ── 关闭时自动断开 ── */
    @PreDestroy
    public void cleanup() {
        if (client != null) {
            client.close();
            log.info("[InfluxDB] 已断开");
        }
    }
}
