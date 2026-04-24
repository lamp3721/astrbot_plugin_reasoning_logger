# astrbot_plugin_gemini_thinks_filtering

打印 AstrBot 已提取到 `LLMResponse.reasoning_content` 的思考内容。

## 说明

这个插件不解析 `<think>` 标签。

它直接读取：

```python
resp.reasoning_content
```

所以只要某个 provider 已经把思考内容标准化到这个字段，插件就能打印。

## 用途

- 查看被框架隐藏的思考内容
- 调试 provider 是否正确提取 reasoning
- 观察模型真实思考输出


## 限制

- 只打印日志，不主动发送给用户
- 依赖 provider 已写入 `resp.reasoning_content`
