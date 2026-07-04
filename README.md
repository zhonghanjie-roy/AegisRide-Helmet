# AegisRide Helmet

基于 UniKnect Gen1 Pro 的智能骑行安全头盔  
An IoT-based cycling safety helmet powered by UniKnect Gen1 Pro, MicroPython, 4G and GNSS.

## 项目简介

AegisRide Helmet 是一个面向骑行安全场景的智能头盔项目，基于 Quectel UniKnect Gen1 Pro 开发套件和 MicroPython 开发环境，计划集成环境感知、运动状态检测、定位追踪、远程数据上传和异常预警等功能。

本项目用于参加全国大学生嵌入式芯片与系统设计竞赛，选题方向为“智能骑行头盔”。

## 核心功能规划

- [ ] 环境数据采集：温湿度、光照等骑行环境信息
- [ ] 运动状态检测：基于加速度传感器识别骑行状态和异常冲击
- [ ] GNSS 定位：获取骑行位置数据
- [ ] 4G 网络通信：上传传感器数据和定位信息
- [ ] 异常预警：跌倒、碰撞或长时间静止时触发报警逻辑
- [ ] 本地数据记录：保存关键传感器和事件数据
- [ ] 可视化展示：后续接入 Web 页面或移动端展示数据

## 技术栈

| 类型 | 内容 |
|---|---|
| 开发板 | UniKnect Gen1 Pro |
| 主控 | STM32 NUCLEO-F413ZH |
| 通信模块 | EC200U 4G Cat.1 |
| 开发语言 | MicroPython |
| 开发工具 | Thonny |
| 网络能力 | TCP / HTTP / MQTT |
| 定位能力 | GNSS |
| 传感器 | 光敏、温湿度、加速度、心率模块等 |

## 项目结构

```text
AegisRide-Helmet/
├── firmware/        # MicroPython 程序代码
├── hardware/        # 硬件接线图、模块说明、实物图
├── docs/            # 项目文档、测试记录、答辩材料
├── images/          # 项目展示图片
└── README.md        # 项目说明
