# Firmware

本目录存放 AegisRide Helmet 的 MicroPython / QuecPython 设备端程序。当前主线版本为 V3，负责多传感器采集、碰撞检测、省电模式和 MQTT 数据上传。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `main.py` | 主程序入口，负责初始化、调度任务和汇总遥测数据 |
| `boot.py` | 设备启动脚本 |
| `tim2.py` | Timer2 任务标志位调度 |
| `bmi160.py` | BMI160 驱动与碰撞检测 |
| `Head_rate.py` | MAX30102 驱动与心率估计 |
| `gnss.py` | GNSS 后台读取、速度滤波和缓存 |
| `temp_humi.py` | AHT20 温湿度读取 |
| `MQTT_V3.py` | EC200U 网络初始化、MQTT 长连接、快速发布和重连 |
| `i2c_init.py` | 共享 I2C 总线初始化 |
| `buzzer.py` | 蜂鸣器控制 |

## 运行环境

| 项目 | 内容 |
| --- | --- |
| 开发板 | UniKnect Gen1 Pro + STM32 NUCLEO-F413ZH |
| 开发语言 | MicroPython / QuecPython |
| 开发工具 | Thonny |
| 开发系统 | macOS |

## 运行方法

1. 使用 Micro USB 将 STM32 NUCLEO-F413ZH 连接到电脑。
2. 打开 Thonny，选择对应解释器和串口。
3. 将本目录下 `.py` 文件上传到设备文件系统。
4. 检查 `MQTT_V3.py` 中的 `MQTT_SERVER`、`MQTT_PORT`、`CLIENT_ID` 和 `TOPIC`。
5. 运行 `main.py`。
6. 在 Shell 窗口查看 BMI160、GNSS、AHT20、MQTT 等输出。

## 传感器地址

| 模块 | 默认地址 |
| --- | --- |
| BMI160 | `0x69` |
| MAX30102 | `0x57` |
| AHT20 | `0x38` |

## 任务周期

| 任务 | 周期 |
| --- | ---: |
| 碰撞检测 | 40 ms |
| 心率采样 | 40 ms |
| GNSS 缓存读取 | 800 ms |
| MQTT 数据写入 | 1 s |
| 心率计算 | 3 s |
| 温湿度读取 | 600 s |

## MQTT 数据

每秒发布一次逗号分隔定点整数：

```text
heart_rate,temperature,humidity,longitude,latitude,speed,collision
```

字段缩放规则见 [../docs/DATA_PROTOCOL.md](../docs/DATA_PROTOCOL.md)。

## 注意事项

- 运行前确认开发板和 4G 模块供电稳定。
- 确认 S502 拨到 ARDU / MCU 侧，使 STM32 可读取板载传感器。
- 如果 I2C 扫描不到 MAX30102，请检查供电、SCL、SDA 和共地。
- 碰撞阈值需要结合真实佩戴方式和路面震动继续标定。
- 上线前建议关闭高频调试打印。
- 不要将真实 MQTT 密码、服务器密钥或个人轨迹上传到公开仓库。
