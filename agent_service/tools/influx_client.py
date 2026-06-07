
import os

from influxdb_client import InfluxDBClient

# ── 连接信息，优先读环境变量，读不到用默认值 ──
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "dayagent-dev-token")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "dayagent")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "sensors")

# 全局客户端，复用连接
_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)


def query_recent(minutes: int = 60) -> list[dict]:
    """查最近 N 分钟的环境数据"""
    query_api = _client.query_api()
    flux = f"""
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -{minutes}m)
        |> filter(fn: (r) => r._measurement == "sensor_readings")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> sort(columns: ["_time"])
    """
    result = query_api.query(flux)
    rows = []
    for table in result:
        for record in table.records:
            row = {"time": record.get_time().isoformat()}
            for field in ["temperature", "humidity", "co2", "light", "pm25"]:
                row[field] = record.values.get(field)
            rows.append(row)
    return rows


def query_latest() -> dict | None:
    """查最新一条传感器数据"""
    query_api = _client.query_api()
    flux = f"""
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -5m)
        |> filter(fn: (r) => r._measurement == "sensor_readings")
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: 1)
    """
    result = query_api.query(flux)
    for table in result:
        for record in table.records:
            row = {"time": record.get_time().isoformat()}
            for field in ["temperature", "humidity", "co2", "light", "pm25"]:
                row[field] = record.values.get(field)
            return row
    return None
