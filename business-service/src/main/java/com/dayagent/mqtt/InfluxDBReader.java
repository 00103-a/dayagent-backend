package com.dayagent.mqtt;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.InfluxDBClientFactory;
import com.influxdb.client.InfluxDBClientOptions;
import com.influxdb.query.FluxRecord;
import com.influxdb.query.FluxTable;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * InfluxDB 读取器
 * 从 InfluxDB 查询最新的传感器数据，替代 SensorController 里的假数据
 */
@Component
public class InfluxDBReader {

    private static final Logger log = LoggerFactory.getLogger(InfluxDBReader.class);

    @Value("${influxdb.url}")
    private String url;

    @Value("${influxdb.token}")
    private String token;

    @Value("${influxdb.org}")
    private String org;

    @Value("${influxdb.bucket}")
    private String bucket;

    private InfluxDBClient client;

    @PostConstruct
    public void init() {
        InfluxDBClientOptions options = InfluxDBClientOptions.builder()
                .url(url)
                .authenticateToken(token.toCharArray())
                .org(org)
                .bucket(bucket)
                .build();
        this.client = InfluxDBClientFactory.create(options);
        log.info("[InfluxDBReader] 已连接 {} (bucket={})", url, bucket);
    }

    /**
     * 查询最新一条传感器数据
     * 和 Python 版 query_latest() 查询逻辑一致
     */
    public Map<String, Object> queryLatest() {
        String flux = """
            from(bucket: "%s")
                |> range(start: -5m)
                |> filter(fn: (r) => r._measurement == "sensor_readings")
                |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: true)
                |> limit(n: 1)
            """.formatted(bucket);

        try {
            List<FluxTable> tables = client.getQueryApi().query(flux);
            for (FluxTable table : tables) {
                for (FluxRecord record : table.getRecords()) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    // 只取我们关心的 5 个字段
                    for (String field : new String[]{"temperature", "humidity", "co2", "light", "pm25"}) {
                        Object val = record.getValueByKey(field);
                        row.put(field, val instanceof Number ? ((Number) val).doubleValue() : null);
                    }
                    log.debug("[InfluxDBReader] 查询到: temp={}, hum={}", row.get("temperature"), row.get("humidity"));
                    return row;
                }
            }
        } catch (Exception e) {
            log.warn("[InfluxDBReader] 查询失败: {}", e.getMessage());
        }
        return null; // InfluxDB 里没数据时返回 null
    }

    @PreDestroy
    public void cleanup() {
        if (client != null) {
            client.close();
            log.info("[InfluxDBReader] 已断开");
        }
    }
}
