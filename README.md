# AegisRide Helmet

基于 UniKnect Gen1 Pro 的智能骑行安全头盔  
An IoT-based cycling safety helmet powered by UniKnect Gen1 Pro, MicroPython, 4G, GNSS and a WeChat Mini Program dashboard.

---

## 项目简介

AegisRide Helmet 是一套面向骑行安全场景的智能头盔原型系统。项目以 STM32 NUCLEO-F413ZH 和 Quectel UniKnect Gen1 Pro / EC200U 为核心，集成 BMI160 六轴惯性传感器、MAX30102 心率传感器、AHT20 温湿度传感器、GNSS 定位、4G MQTT 通信、蜂鸣器和按键交互。

系统目标是构建完整的“端侧感知 -> 本地判断 -> 4G 上传 -> 云端接口 -> 小程序展示 -> 安全确认”闭环，用于骑行状态监测、碰撞预警、位置追踪、亲友守护和竞赛展示。

本项目用于参加全国大学生嵌入式芯片与系统设计竞赛，选题方向为“智能骑行头盔”。

---

## 核心功能

- 多传感采集：心率、温湿度、IMU、GNSS 位置和速度。
- 碰撞检测：基于 BMI160 的冲击检测和静止确认逻辑，40 ms 周期运行。
- 本地报警：碰撞状态锁存后驱动蜂鸣器报警，按键可解除告警。
- 省电模式：长按按键切换正常 / 省电模式，省电时保留碰撞检测和 MQTT 上传。
- 4G 通信：EC200U 蜂窝网络，MQTT 长连接上传遥测数据。
- 小程序联动：展示实时状态、心率趋势、天气、轨迹、碰撞提醒和“本人安全”确认。
- 云端接口：支持最新数据、历史数据、设备状态、告警列表和安全确认接口。

---

## 技术栈

| 类型 | 内容 |
| --- | --- |
| 开发套件 | Quectel UniKnect Gen1 Pro / QADP-EC200U-Arduino |
| 主控板 | STM32 NUCLEO-F413ZH |
| 通信模块 | EC200U 4G Cat.1 |
| 运行环境 | MicroPython / QuecPython |
| 开发工具 | Thonny |
| 网络通信 | 4G、MQTT、HTTP API |
| 定位能力 | GNSS |
| 传感器 | BMI160、MAX30102、AHT20 |
| 前端展示 | 微信小程序 |
| 本地调试服务 | Node.js + Express |

---

## 系统架构

```text
┌────────────────────────────────────────────┐
│              AegisRide Helmet              │
├────────────────────────────────────────────┤
│ Sensor Layer                               │
│ - BMI160 IMU                               │
│ - MAX30102 Heart Rate                      │
│ - AHT20 Temperature / Humidity             │
│ - GNSS Positioning                         │
├────────────────────────────────────────────┤
│ Control Layer                              │
│ - STM32 NUCLEO-F413ZH                      │
│ - RTOS-like Timer2 Scheduling              │
│ - Collision Detection / Power Save State   │
├────────────────────────────────────────────┤
│ Communication Layer                        │
│ - EC200U 4G Cat.1                          │
│ - MQTT Long Connection                     │
│ - Fixed-point Telemetry Encoding           │
├────────────────────────────────────────────┤
│ Application Layer                          │
│ - Cloud Broker / API / Database            │
│ - WeChat Mini Program Dashboard            │
│ - Family Safety Confirmation               │
└────────────────────────────────────────────┘
```

详细设计见 [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)。

---

## 端侧任务周期

| 任务 | 周期 | 说明 |
| --- | ---: | --- |
| 碰撞检测 | 40 ms | 读取 BMI160，判断冲击和碰撞状态 |
| 心率采样 | 40 ms | 读取 MAX30102 FIFO 并预处理 |
| GNSS 缓存读取 | 800 ms | 更新经纬度、速度和卫星状态 |
| MQTT 数据写入 | 1 s | 将最新遥测数据交给通信线程 |
| 心率计算 | 3 s | 计算 BPM |
| 温湿度读取 | 600 s | 低频采集环境温湿度 |

---

## 目录结构

```text
.
├── README.md
├── docs/
│   ├── SYSTEM_DESIGN.md
│   ├── DATA_PROTOCOL.md
│   ├── TEST_PLAN.md
│   ├── ROADMAP.md
│   └── dev-log.md
├── firmware/
│   ├── main.py
│   ├── MQTT_V3.py
│   ├── bmi160.py
│   ├── Head_rate.py
│   ├── gnss.py
│   ├── temp_humi.py
│   ├── tim2.py
│   └── README.md
├── hardware/
│   └── wiring.md
└── images/
```

---

## 快速开始

### 1. 准备硬件

1. 将 UniKnect Gen1 Pro 与 STM32 NUCLEO-F413ZH 通过 Arduino 接口堆叠。
2. 连接 4G 天线和 GNSS 天线。
3. 接入 MAX30102 心率模块。
4. 确认 I2C 地址和供电稳定。

硬件连接见 [hardware/wiring.md](hardware/wiring.md)。

### 2. 上传固件

1. 使用 Thonny 连接开发板。
2. 将 `firmware/` 目录内的 `.py` 文件上传到设备。
3. 检查 `MQTT_V3.py` 中的 Broker、Topic 和设备编号。
4. 运行 `main.py` 并查看串口输出。

固件说明见 [firmware/README.md](firmware/README.md)。

### 3. 对接云端和小程序

设备端 MQTT payload 采用逗号分隔定点整数格式。云端订阅后应解析为心率、温湿度、经纬度、速度和碰撞状态，再提供 HTTP API 给小程序读取。

接口与数据格式见 [docs/DATA_PROTOCOL.md](docs/DATA_PROTOCOL.md)。

---

## 测试与验证

建议按以下顺序验证：

1. I2C 扫描。
2. BMI160 原始数据与碰撞阈值。
3. MAX30102 心率采样。
4. AHT20 温湿度读取。
5. GNSS 定位与速度滤波。
6. EC200U 网络注册和 MQTT 发布。
7. 小程序实时状态刷新。
8. 碰撞模拟、蜂鸣器报警和安全确认。

详细测试计划见 [docs/TEST_PLAN.md](docs/TEST_PLAN.md)。

---

## 当前状态

- 已完成嵌入式 V3 主线代码。
- 已完成 Timer2 多周期调度。
- 已完成 BMI160、MAX30102、AHT20、GNSS、MQTT 模块集成。
- 已完成碰撞报警锁存和按键解除逻辑。
- 已完成小程序看板和本地调试 API 的设计与联调基础。

---

## 安全与隐私

公开仓库前请确认不包含以下内容：

- MQTT 用户名、密码、私有 Broker 凭据。
- 云服务器密钥、数据库连接串、API Token。
- 微信小程序 AppSecret 或私有配置。
- 骑行者真实姓名、电话、精确轨迹等个人信息。

---

## License

当前仓库尚未声明开源许可证。公开复用前请补充合适的 `LICENSE` 文件。
