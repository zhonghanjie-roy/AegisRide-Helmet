# Firmware

本目录存放 AegisRide Helmet 项目的 MicroPython 程序代码。

## 文件说明

| 文件 | 作用 |
|---|---|
| `main.py` | 项目主程序入口 |
| `config.example.py` | 配置文件模板，用于填写服务器地址、端口等参数 |

## 运行环境

| 项目 | 内容 |
|---|---|
| 开发板 | UniKnect Gen1 Pro + STM32 NUCLEO-F413ZH |
| 开发语言 | MicroPython |
| 开发工具 | Thonny |
| 开发系统 | macOS |

## 运行方法

1. 使用 Micro USB 将 STM32 NUCLEO-F413ZH 连接到电脑。
2. 打开 Thonny。
3. 选择 MicroPython 解释器和对应串口。
4. 打开 `main.py`。
5. 点击运行按钮。
6. 在 Shell 窗口查看传感器、网络或定位数据输出。

## 注意事项

- 运行前请确认开发板已正常供电。
- 如果需要读取板载 I2C 传感器，请确认 S502 拨到 ARDU / MCU 侧。
- 如果使用 MAX30102，请确认 I2C 扫描可以识别到 `0x57`。
- 如果代码中需要配置服务器地址、MQTT 参数或 HTTP 接口，请复制 `config.example.py` 并按实际情况修改为 `config.py`。
- 不建议将真实密钥、密码或个人信息上传到公开仓库。
