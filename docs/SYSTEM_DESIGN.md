# System Design

本文说明 AegisRide Helmet 的系统设计、模块职责和运行流程。

## 1. 设计目标

AegisRide Helmet 面向真实骑行安全场景，目标是让头盔具备独立感知、独立联网和远程告警能力。系统不依赖手机作为唯一通信中继，设备端可通过 4G 网络上传位置、速度、心率、环境状态和碰撞告警。

核心目标：

- 实时采集骑行者和环境数据。
- 在端侧快速识别疑似碰撞。
- 通过蜂鸣器和小程序形成双通道提醒。
- 支持亲友远程查看状态并确认安全。
- 保留低功耗模式，延长设备可用时间。

## 2. 分层架构

```text
Sensor Layer
  BMI160 / MAX30102 / AHT20 / GNSS
        ↓
Scheduling Layer
  Timer2 flags, fixed-period tasks
        ↓
Processing Layer
  Collision detection, heart-rate estimation, speed filtering
        ↓
Communication Layer
  EC200U 4G, MQTT long connection
        ↓
Application Layer
  Cloud API, database, WeChat Mini Program
```

## 3. 主要模块

| 模块 | 文件 | 职责 |
| --- | --- | --- |
| 主程序 | `firmware/main.py` | 初始化、任务调度、省电模式、数据汇总 |
| 定时器 | `firmware/tim2.py` | 产生 40 ms、800 ms、1 s、3 s、600 s 标志位 |
| IMU | `firmware/bmi160.py` | BMI160 初始化、读取和碰撞检测 |
| 心率 | `firmware/Head_rate.py` | MAX30102 FIFO 读取、滤波和 BPM 估计 |
| GNSS | `firmware/gnss.py` | 后台定位、速度滤波和缓存 |
| 温湿度 | `firmware/temp_humi.py` | AHT20 初始化和读取 |
| MQTT | `firmware/MQTT_V3.py` | EC200U 网络、MQTT 连接、快速发布和重连 |
| 蜂鸣器 | `firmware/buzzer.py` | 本地报警输出 |
| I2C | `firmware/i2c_init.py` | 统一 I2C 总线初始化 |

## 4. 调度机制

系统采用 RTOS-like 标志位调度，而不是在主循环中直接阻塞等待。Timer2 周期性设置任务标志，主循环检查并消费标志位。

任务周期：

| 标志 | 周期 | 任务 |
| --- | ---: | --- |
| `flag_40ms` | 40 ms | 碰撞检测、按键检测 |
| `flag1_40ms` | 40 ms | 心率采样 |
| `flag_800ms` | 800 ms | GNSS 缓存读取 |
| `flag_1s` | 1 s | 写入 MQTT 共享变量 |
| `flag_3s` | 3 s | 心率 BPM 计算 |
| `flag_600s` | 600 s | 温湿度读取 |

这种设计将不同耗时任务拆开，避免 GNSS、MQTT 或温湿度读取阻塞碰撞检测。

## 5. 碰撞检测逻辑

当前 V3 逻辑基于 BMI160 的加速度和角速度数据，采用双阶段判断：

1. 冲击识别：加速度平方和、角速度平方和超过阈值。
2. 状态确认：在窗口内持续观察是否进入稳定/静止状态。

一旦判定为有效碰撞：

- `bmi160.st_flag` 被锁存为 `1`。
- 主循环驱动蜂鸣器持续报警。
- MQTT 数据中的 `collision` 字段上传为 `1`。
- 小程序端根据告警状态弹窗提醒。

解除方式：

- 用户按下头盔按键解除本地报警。
- 小程序端点击“本人安全”，云端清除告警状态。

## 6. 省电模式

用户长按按键约 2 秒切换省电模式：

- 正常模式：心率、GNSS、温湿度、碰撞检测、MQTT 都运行。
- 省电模式：暂停心率、GNSS、温湿度，保留碰撞检测和 MQTT。

主程序通过 `save_flag` 控制任务是否执行。省电模式下湿度字段置为 `0`，小程序可据此显示省电状态。

## 7. 通信设计

MQTT 线程独立运行，负责：

- 初始化 EC200U 网络。
- 检查 SIM 卡和蜂窝网络注册。
- 建立 MQTT 长连接。
- 每秒发布最新遥测数据。
- 断线后释放资源并重连。

V3 版本对 MQTT QoS0 发布进行了优化：直接构造 PUBLISH 报文并通过 socket 单次写入，减少底层发送次数。

## 8. 小程序交互

小程序端核心页面展示：

- 心率、温度、湿度、速度。
- 设备在线状态和碰撞状态。
- 地图定位和骑行轨迹。
- 天气和空气质量。
- 碰撞弹窗和“本人安全”按钮。

推荐云端接口见 [DATA_PROTOCOL.md](DATA_PROTOCOL.md)。
