# Hardware Wiring Guide

本文件记录 AegisRide Helmet 智能骑行头盔项目的硬件连接方式，包括开发板堆叠、供电、板载传感器、MAX30102 心率模块、天线和调试接口说明。

---

## 1. 硬件组成

| 模块 | 型号 / 名称 | 作用 |
|---|---|---|
| 主控开发板 | STM32 NUCLEO-F413ZH | 运行 MicroPython 程序，负责传感器采集、逻辑判断和外设控制 |
| 扩展板 | UniKnect Gen1 Pro / QADP-EC200U-Arduino | 提供 4G 通信、GNSS、板载传感器和 Arduino 扩展接口 |
| 蜂窝通信模块 | EC200U | 4G Cat.1 网络通信，用于远程数据上传 |
| 温湿度传感器 | AH20-F | 采集骑行环境温度和湿度 |
| 三轴加速度传感器 | LIS2DH12TR | 采集运动姿态、冲击、跌倒等状态数据 |
| 光敏电阻 | GL5528 | 采集环境光照强度 |
| 心率模块 | MAX30102 | 采集心率相关原始数据 |
| LTE 天线 | 蜂窝天线 | EC200U 蜂窝网络信号收发 |
| GNSS 天线 | GNSS 天线 | GNSS 定位信号接收 |
| 开发工具 | Thonny | MicroPython 程序编写、运行和调试 |

---

## 2. 整体硬件连接关系

```text
┌────────────────────────────────────────────┐
│              AegisRide Helmet              │
├────────────────────────────────────────────┤
│ STM32 NUCLEO-F413ZH                         │
│ - 运行 MicroPython                          │
│ - 读取传感器数据                            │
│ - 执行安全预警逻辑                          │
├────────────────────────────────────────────┤
│ UniKnect Gen1 Pro / QADP-EC200U-Arduino     │
│ - EC200U 4G 通信                            │
│ - GNSS 定位                                 │
│ - 板载温湿度 / 加速度 / 光敏传感器           │
│ - Arduino UNO 标准接口                      │
├────────────────────────────────────────────┤
│ External Sensor                             │
│ - MAX30102 Heart Rate Sensor                │
└────────────────────────────────────────────┘
```

---

## 3. UniKnect Gen1 Pro 与 STM32 NUCLEO-F413ZH 连接

### 3.1 连接方式

UniKnect Gen1 Pro 扩展板通过 Arduino UNO 标准接口与 STM32 NUCLEO-F413ZH 开发板垂直堆叠连接。

```text
UniKnect Gen1 Pro Arduino UNO 接口
                 ↓
STM32 NUCLEO-F413ZH Arduino UNO 接口
```

### 3.2 操作方法

1. 确认两块开发板断电。
2. 将 UniKnect Gen1 Pro 扩展板的 Arduino 排针与 STM32 NUCLEO-F413ZH 的 Arduino 排母对齐。
3. 垂直向下插入，确保所有排针完全插入。
4. 检查是否有插偏、错位或排针悬空。
5. 上电前再次确认 USB 线、天线和外接模块连接无误。

### 3.3 为什么这样接

- Arduino UNO 标准接口可以直接完成两块开发板之间的 UART、I2C、ADC、GPIO 和部分电源信号连接。
- 垂直堆叠比杜邦线连接更稳定，减少接线错误。
- STM32 作为主控运行 MicroPython，UniKnect Gen1 Pro 作为通信和传感器扩展板，结构清晰。

---

## 4. 供电连接

### 4.1 推荐供电方式

| 接口 | 作用 | 当前项目用途 |
|---|---|---|
| STM32 NUCLEO Micro USB | 给 STM32 供电、烧录固件、Thonny 调试 | 必接 |
| UniKnect Gen1 Pro J401 Type-C | EC200U 模组 USB 通信 / AT 调试 / 模组供电 | 推荐连接 |
| UniKnect Gen1 Pro J403 Type-C | USB 转 TTL 串口 / 5V 供电 | 调试时可用 |
| UniKnect Gen1 Pro J201 DC 口 | 外部 5V 电源输入 | 需要更稳定供电时使用 |

当前项目推荐连接：

```text
STM32 NUCLEO-F413ZH Micro USB  →  Mac 电脑
UniKnect Gen1 Pro J401 Type-C  →  Mac 电脑 / 5V USB 电源
```

如果 4G 模组联网不稳定，建议额外使用：

```text
UniKnect Gen1 Pro J201 DC 5V  →  5V / 2A 电源适配器
```

### 4.2 S201 电源选择

如果使用 J201 / J401 / J403 给 QADP 板供电：

```text
S201 → 拨到 DC / USB 侧
```

如果使用 Arduino 接口给 QADP 板供电：

```text
S201 → 拨到 ARDU 侧
```

本项目推荐：

```text
S201 → DC / USB 侧
```

### 4.3 为什么这样接

- STM32 NUCLEO 的 Micro USB 用于 Thonny 连接、程序运行和调试。
- UniKnect Gen1 Pro 上的 EC200U 4G 模组需要稳定供电。
- 4G 模组在联网、注册网络和数据发送时可能出现较大瞬时电流。
- 如果只依赖 Arduino 接口供电，可能出现带载能力不足，导致模组重启、联网失败或串口异常。
- 因此，QADP / UniKnect Gen1 Pro 侧优先使用 Type-C 或 DC 5V 供电。

---

## 5. 板载传感器连接

UniKnect Gen1 Pro 板载以下传感器：

| 传感器 | 连接方式 | 用途 |
|---|---|---|
| AH20-F 温湿度传感器 | I2C | 环境温度、湿度采集 |
| LIS2DH12TR 三轴加速度传感器 | I2C + INT | 姿态、运动、冲击和跌倒检测 |
| GL5528 光敏电阻 | ADC | 环境光照强度采集 |

### 5.1 S502 开关设置

S502 用于选择板载 I2C 传感器连接到 MCU 侧还是 EC200U 模组侧。

当前项目由 STM32 运行 MicroPython 程序并读取传感器数据，因此：

```text
S502 → ARDU / MCU 侧
```

### 5.2 板载 I2C 接口

| QADP 接口 | 功能 |
|---|---|
| J302-9pin | I2C SCL |
| J302-10pin | I2C SDA |

当 S502 拨到 ARDU 位置时，板载 AH20-F 温湿度传感器和 LIS2DH12TR 三轴加速度传感器通过 J302-9pin、J302-10pin 与 STM32 通信。

### 5.3 光敏电阻 ADC

| QADP 接口 | 功能 |
|---|---|
| J303-1pin | ADC 输入，用于采集光敏电阻 R316 的电压变化 |

### 5.4 为什么这样接

- 本项目的控制逻辑运行在 STM32 上。
- 将 S502 拨到 ARDU / MCU 侧后，STM32 可以直接读取板载 I2C 传感器。
- 温湿度数据可用于骑行环境感知。
- 加速度数据可用于判断骑行状态、冲击、跌倒和异常静止。
- 光照数据可用于夜间骑行判断，后续可扩展自动灯光或夜间安全提醒。

---

## 6. MAX30102 心率模块连接

MAX30102 是本项目外接的人体状态检测模块，用于采集心率相关原始数据。该模块通过 I2C 与 STM32 主控通信，因此需要连接电源、地线、SCL 和 SDA。INT 中断脚当前阶段可先不接，后续需要实时采样或低功耗优化时再接入 GPIO。

---

### 6.1 MAX30102 实际接线表

> 注意：不同 MAX30102 模块板的丝印可能略有差异，接线时以模块板实际丝印为准。常见丝印包括 VCC、VIN、3V3、GND、SCL、SDA、INT。

| MAX30102 模块引脚 | 连接到开发板 | 作用 |
|---|---|---|
| VCC / VIN | 3.3V | 给 MAX30102 模块供电 |
| GND | GND | 与 STM32 共地 |
| SCL | J302-9pin / I2C SCL | I2C 时钟线 |
| SDA | J302-10pin / I2C SDA | I2C 数据线 |
| INT | 暂不连接 / 后续接 GPIO | 中断输出，当前轮询读取时可不接 |

---

### 6.2 当前项目接法

```text
MAX30102 VCC / VIN  →  3.3V
MAX30102 GND        →  GND
MAX30102 SCL        →  J302-9pin / I2C SCL
MAX30102 SDA        →  J302-10pin / I2C SDA
MAX30102 INT        →  暂不连接
```

如果模块上丝印是 `3V3` 而不是 `VCC`：

```text
MAX30102 3V3  →  3.3V
MAX30102 GND  →  GND
MAX30102 SCL  →  J302-9pin / I2C SCL
MAX30102 SDA  →  J302-10pin / I2C SDA
```

---

### 6.3 为什么这样接

#### 1. SCL / SDA 是 I2C 通信线

MAX30102 使用 I2C 接口通信：

| 信号 | 作用 |
|---|---|
| SCL | Serial Clock，串行时钟线 |
| SDA | Serial Data，串行数据线 |

STM32 作为 I2C 主机，通过 SCL 提供时钟，通过 SDA 读写 MAX30102 内部寄存器和 FIFO 数据。

#### 2. VCC 接 3.3V

本项目使用常见 MAX30102 模块板，而不是裸芯片。常见模块板通常已经集成稳压电路和 I2C 上拉电阻，因此推荐接 3.3V。

```text
推荐：3.3V
不推荐：5V
```

这样做可以降低损坏 STM32 I/O 或 MAX30102 模块的风险。

#### 3. GND 必须共地

STM32 和 MAX30102 必须共地：

```text
STM32 GND ↔ MAX30102 GND
```

如果没有共地，SCL / SDA 的高低电平没有共同参考点，I2C 通信会失败。

#### 4. INT 当前可以不接

MAX30102 的 INT 是低电平有效中断输出。当前阶段采用轮询方式读取数据，因此先不接 INT。

后续如果需要优化：

- 实时心率采样
- 低功耗唤醒
- 数据准备完成后再读取
- 减少无效轮询

可以将 INT 接到 STM32 的一个 GPIO 输入脚。

#### 5. 与板载传感器共用 I2C 总线

MAX30102 可以与板载温湿度传感器、加速度传感器共用同一条 I2C 总线，只要地址不冲突即可。

本项目中：

```text
板载 AH20-F / LIS2DH12TR → I2C 总线
MAX30102                → 同一 I2C 总线
```

---

### 6.4 MAX30102 地址说明

MAX30102 的 7 位 I2C 地址为：

```text
0x57
```

对应 8 位地址：

```text
Write Address: 0xAE
Read Address : 0xAF
```

在 MicroPython 的 I2C 扫描程序中，一般会显示 7 位地址：

```text
0x57
```

---

### 6.5 接线检查清单

| 检查项 | 正确状态 |
|---|---|
| VCC / VIN | 接 3.3V |
| GND | 接 GND |
| SCL | 接 J302-9pin / I2C SCL |
| SDA | 接 J302-10pin / I2C SDA |
| INT | 当前可不接 |
| S502 | 如果读取板载 I2C 传感器，应拨到 ARDU / MCU 侧 |
| I2C 地址 | 扫描到 0x57 |

---

### 6.6 注意事项

- 如果使用的是 MAX30102 裸芯片，不能直接按模块板接法接 3.3V，因为裸芯片 VDD 典型工作电压为 1.8V，LED 电源 VLED+ 典型为 3.3V。
- 如果使用的是常见 MAX30102 模块板，应以模块丝印为准，优先使用 3.3V、GND、SCL、SDA。
- 不建议把 I2C 信号线直接接 5V。
- 如果 I2C 扫描不到设备，优先检查 SCL / SDA 是否接反。
- 如果板载 I2C 传感器也需要读取，确认 S502 已拨到 ARDU / MCU 侧。
- 如果总线上多个 I2C 设备地址冲突，需要更换设备或调整硬件方案。

---

### 6.7 MAX30102 验证方法

在 Thonny 中运行 I2C 扫描程序。

如果接线正确，应能看到：

```text
0x57
```

验证结果记录：

| 测试项 | 结果 |
|---|---|
| MAX30102 供电 | 已完成 |
| GND 共地 | 已完成 |
| I2C 扫描 | 已通过 |
| 心率模块基础读取 | 已通过 |

---

## 7. 天线连接

### 7.1 天线接口说明

| 接口 | 连接对象 | 作用 |
|---|---|---|
| J101 | LTE 蜂窝天线 | 4G 网络通信 |
| J102 | GNSS 天线 | GNSS 定位 |
| J103 | WiFi Scan 天线 | 辅助定位，当前项目可暂不使用 |

### 7.2 当前项目连接

```text
J101 → LTE 蜂窝天线
J102 → GNSS 天线
J103 → 暂不连接
```

### 7.3 为什么这样接

- EC200U 进行 4G 网络注册和数据上传时需要 LTE 天线。
- GNSS 定位需要连接 GNSS 天线。
- GNSS 测试应尽量在室外或靠近窗边的开阔环境进行。
- WiFi Scan 主要用于辅助定位，当前智能骑行头盔核心功能暂不依赖该接口。

---

## 8. SIM 卡与网络连接

### 8.1 SIM 卡选择

UniKnect Gen1 Pro / QADP 板支持：

| SIM 类型 | 说明 |
|---|---|
| eSIM | 板载贴片物联网卡 |
| Nano SIM | 外部插拔 SIM 卡 |

通过 S501 切换：

```text
S501 → ESIM
```

或：

```text
S501 → USIM
```

### 8.2 当前项目建议

如果板载 eSIM 可正常联网，优先使用：

```text
S501 → ESIM
```

如果需要使用自己的流量卡：

```text
S501 → USIM
```

### 8.3 注意事项

- 模组开机状态下切换 SIM 卡后，可能需要重新开机。
- 也可以通过 AT+CFUN=0、AT+CFUN=1 重新识别 SIM。
- 如果 4G 无法注册网络，先检查天线、SIM 卡、供电和信号环境。

---

## 9. 串口与调试连接

### 9.1 调试接口说明

| 接口 | 作用 |
|---|---|
| STM32 NUCLEO Micro USB | Thonny 连接 MicroPython 解释器、烧录和调试 |
| J401 Type-C | EC200U 模组 USB 通信、AT 调试、模组固件升级 |
| J403 Type-C | USB 转 TTL 串口调试 |
| J305 | 预留监控 MCU 与 EC200U 串口通信 |
| J308 | Arduino / MCU 串口选择 |

### 9.2 当前项目使用方式

```text
STM32 NUCLEO Micro USB → Mac → Thonny
UniKnect Gen1 Pro J401 Type-C → Mac / 5V USB 电源
```

### 9.3 为什么这样接

- Thonny 主要通过 STM32 NUCLEO 的调试串口连接 MicroPython。
- J401 可用于 EC200U 模组调试、AT 命令测试或固件升级。
- J403 / J305 可用于观察 MCU 与 EC200U 之间的串口通信，便于排查 4G 通信问题。
- 调试阶段建议先保证 Thonny 能稳定连接 STM32，再逐步测试 4G 和 GNSS。

---

## 10. 当前接线状态

| 模块 | 状态 | 说明 |
|---|---|---|
| STM32 NUCLEO-F413ZH | 已连接 | 可通过 Thonny 运行 MicroPython |
| UniKnect Gen1 Pro | 已连接 | 与 STM32 通过 Arduino 接口堆叠 |
| 板载温湿度传感器 | 已测试 | 可读取基础数据 |
| 板载加速度传感器 | 已测试 | 可读取基础数据 |
| 板载光敏电阻 | 已测试 | 可读取 ADC 数据 |
| MAX30102 心率模块 | 已测试 | 可扫描到 I2C 设备并读取基础数据 |
| LTE 天线 | 已连接 | 用于 4G 通信 |
| GNSS 天线 | 已连接 | 用于定位测试 |
| Thonny 调试连接 | 已完成 | macOS 可连接开发板 |

---

## 11. 常见问题排查

### 11.1 Thonny 连接不到开发板

检查：

- Micro USB 是否连接到 STM32 NUCLEO 的 ST-LINK 口
- macOS 是否识别串口
- Thonny 解释器是否选择 MicroPython
- Thonny 端口是否选择正确
- 开发板是否已经烧录 MicroPython 固件

---

### 11.2 MAX30102 扫描不到 0x57

检查：

- VCC 是否接 3.3V
- GND 是否共地
- SCL / SDA 是否接反
- 是否接到了正确的 I2C 引脚
- 模块是否松动
- 模块是否损坏
- I2C 总线是否被其他设备占用
- S502 是否拨到 ARDU / MCU 侧

---

### 11.3 板载温湿度或加速度传感器读不到

检查：

- S502 是否拨到 ARDU / MCU 侧
- I2C 扫描是否能发现设备
- 程序中的 I2C 编号是否正确
- SCL / SDA 是否被外接模块短路
- 外接 MAX30102 是否影响 I2C 总线

---

### 11.4 4G 网络连接失败

检查：

- LTE 天线是否连接到 J101
- S501 是否选择正确 SIM
- SIM 卡是否可用
- 是否欠费或无流量
- QADP 供电是否稳定
- S201 是否拨到正确供电侧
- EC200U 是否已经开机
- NET / MOD 指示灯状态是否正常

---

### 11.5 GNSS 定位失败

检查：

- GNSS 天线是否连接到 J102
- 是否在室内遮挡环境
- 是否靠近窗边或室外测试
- GNSS 是否已经启动
- 是否等待足够长时间完成首次定位

---

## 12. 后续优化

- 补充实际接线照片
- 补充 MAX30102 模块丝印图
- 补充 I2C 扫描截图
- 补充 Thonny 运行截图
- 补充 4G 网络注册测试截图
- 补充 GNSS 定位测试截图
- 补充头盔内部模块安装布局图
- 补充供电方案和移动电源固定方式
