# AegisRide Helmet

基于 UniKnect Gen1 Pro 的智能骑行安全头盔  
An IoT-based intelligent cycling safety helmet powered by UniKnect Gen1 Pro, MicroPython, 4G and GNSS.

---

## 项目简介

AegisRide Helmet 是一款面向骑行安全场景的智能头盔原型系统，基于 Quectel UniKnect Gen1 Pro 开发套件和 MicroPython 开发环境实现。

项目围绕骑行过程中的安全感知、异常检测、位置追踪和远程通信需求，集成了环境传感器、加速度传感器、GNSS 定位、4G 网络通信和心率检测模块，能够采集骑行环境与人体状态数据，并为后续跌倒检测、碰撞预警、远程求助和骑行数据分析提供基础。

本项目用于参加全国大学生嵌入式芯片与系统设计竞赛，选题方向为“智能骑行头盔”。

---

## 核心功能

- 环境数据采集：采集温湿度、光照等骑行环境信息
- 运动状态检测：通过加速度数据判断骑行状态、冲击和异常姿态
- GNSS 定位：获取骑行过程中的经纬度信息
- 4G 网络通信：通过蜂窝网络上传关键数据
- 心率检测：通过 MAX30102 心率模块采集人体状态数据
- 本地数据记录：保存传感器数据和异常事件
- 安全预警逻辑：为跌倒、碰撞、异常静止等场景提供判断基础

---

## 技术栈

| 类型 | 内容 |
|---|---|
| 开发套件 | Quectel UniKnect Gen1 Pro |
| 主控板 | STM32 NUCLEO-F413ZH |
| 通信模块 | EC200U 4G Cat.1 |
| 开发语言 | MicroPython |
| 开发工具 | Thonny |
| 开发系统 | macOS |
| 网络通信 | TCP / HTTP / MQTT |
| 定位能力 | GNSS |
| 传感器 | 温湿度、光照、加速度、MAX30102 心率模块 |

---

## 系统架构

```text
┌────────────────────────────────────┐
│        AegisRide Helmet             │
├────────────────────────────────────┤
│  Sensor Layer                       │
│  - Temperature / Humidity Sensor    │
│  - Light Sensor                     │
│  - Accelerometer                    │
│  - MAX30102 Heart Rate Sensor       │
├────────────────────────────────────┤
│  Control Layer                      │
│  - STM32 NUCLEO-F413ZH              │
│  - MicroPython Runtime              │
├────────────────────────────────────┤
│  Communication Layer                │
│  - EC200U 4G Cat.1                  │
│  - TCP / HTTP / MQTT                │
│  - GNSS Positioning                 │
├────────────────────────────────────┤
│  Application Layer                  │
│  - Data Collection                  │
│  - Abnormal Event Detection         │
│  - Remote Data Upload               │
│  - Riding Safety Warning            │
└────────────────────────────────────┘
