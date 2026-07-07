# Contributing

## 分支建议

- `main`：稳定展示版本。
- `docs/*`：文档补充。
- `firmware/*`：嵌入式固件修改。
- `hardware/*`：硬件连接、结构和测试记录。

## 提交前检查

建议至少完成：

```bash
python -m py_compile firmware/*.py
```

如果修改了硬件相关代码，需要补充：

- 使用的开发板和传感器。
- 接线变化。
- 串口输出。
- 测试场景。

## PR 描述建议

请说明：

- 改动内容。
- 修改原因。
- 验证方式。
- 是否影响 MQTT payload、硬件接线、Topic 或小程序接口。
