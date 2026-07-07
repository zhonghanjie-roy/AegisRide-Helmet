# Data Protocol

本文记录设备端 MQTT 数据格式和小程序 HTTP API 建议。

## 1. MQTT Payload

设备端当前发布逗号分隔定点整数：

```text
heart_rate,temperature,humidity,longitude,latitude,speed,collision
```

示例：

```text
780,264,582,119815200,30248450,520,0
```

## 2. 字段说明

| 字段 | 缩放 | 示例 | 含义 |
| --- | ---: | --- | --- |
| `heart_rate` | x10 | `780` | 78.0 bpm |
| `temperature` | x10 | `264` | 26.4 摄氏度 |
| `humidity` | x10 | `582` | 58.2% |
| `longitude` | x1000000 | `119815200` | 119.815200 |
| `latitude` | x1000000 | `30248450` | 30.248450 |
| `speed` | x100 | `520` | 5.20 m/s |
| `collision` | 0/1 | `0` | 1 表示碰撞告警 |

## 3. 云端解析建议

云端订阅 MQTT topic 后，建议转换为结构化 JSON：

```json
{
  "device_id": "helmet_001",
  "heart_rate": 78.0,
  "temperature": 26.4,
  "humidity": 58.2,
  "longitude": 119.8152,
  "latitude": 30.24845,
  "speed": 5.2,
  "collision": false,
  "created_at": "2026-07-07 22:00:00"
}
```

建议至少保存两类表：

- `sensor_data`：普通遥测数据。
- `alert_event`：碰撞、SOS、心率异常等安全事件。

## 4. 小程序 API 建议

### 最新数据

```http
GET /api/v1/devices/:deviceId/latest
```

返回：

```json
{
  "ok": true,
  "data": {
    "device_id": "helmet_001",
    "heart_rate": 78,
    "temperature": 26.4,
    "humidity": 58.2,
    "latitude": 30.24845,
    "longitude": 119.8152,
    "speed": 5.2,
    "collision": false,
    "network_status": "online",
    "created_at": "2026-07-07 22:00:00"
  }
}
```

### 历史数据

```http
GET /api/v1/devices/:deviceId/history?limit=30
```

用途：

- 心率趋势。
- 地图轨迹。
- 骑行统计。

### 设备状态

```http
GET /api/v1/devices/:deviceId/status
```

返回设备是否在线、最后更新时间和网络状态。

### 告警列表

```http
GET /api/v1/devices/:deviceId/alerts?limit=20
```

告警示例：

```json
{
  "id": 1,
  "device_id": "helmet_001",
  "event_type": "collision",
  "title": "疑似骑手发生碰撞",
  "message": "请立即联系骑手确认安全。",
  "status": "pending",
  "created_at": "2026-07-07 22:00:00"
}
```

### 确认安全

```http
POST /api/v1/devices/:deviceId/self-safe
```

用途：骑手确认本人安全后，云端将未处理碰撞告警标记为已解决。

### 天气代理

```http
GET /api/weather?latitude=30.24845&longitude=119.8152
```

用途：小程序读取当前位置天气、温湿度和空气质量。

## 5. 错误处理建议

统一错误响应：

```json
{
  "ok": false,
  "message": "error message"
}
```

小程序端应处理：

- 网络超时。
- 设备离线。
- 定位授权失败。
- 告警确认失败。
- 天气服务不可用。
