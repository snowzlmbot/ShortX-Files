# ShortX AI 一键指令与自动指令

本仓库新增了三份可导入的 ShortX 文本文件：

- `da/ShortX-AI首次初始化与密钥设置.txt`
- `da/ShortX-AI回合制会话与模型切换.txt`
- `rule/ShortX-AI回合制会话自动指令.txt`

## 导入顺序

1. 导入并运行 `ShortX-AI首次初始化与密钥设置.txt`。
2. 首次配置时填写：

   ```text
   provider|model|protocol|完整请求URL|keyVariableName|skills私有目录
   ```

   默认示例：

   ```text
   OpenAI|gpt-5|openai_responses|https://api.openai.com/v1/responses|shortx_key_openai|/data/data/com.shortx/files/skills
   ```

3. 在随后输入框中填入当前服务商 API Key。Key 只写入对应的 ShortX 隐私全局变量。
4. 从下列地址获取仓库压缩包，并把 `skills/` 解压到上一步填写的 ShortX 私有目录：

   `https://github.com/snowzlmbot/ShortX-Files/archive/refs/heads/main.zip`

5. 导入并启用 `ShortX-AI回合制会话自动指令.txt`，把它绑定到 ShortX 磁贴 1。
6. 导入 `ShortX-AI回合制会话与模型切换.txt`。输入消息后，该一键指令只负责保存本回合；点击磁贴 1 才会发送请求并显示回复。

## 支持的协议分支

- `openai_responses`：使用完整 `/responses` 端点，默认配置为 OpenAI。
- `openai_chat`：使用 OpenAI-compatible `/chat/completions` 端点。
- `anthropic_messages`：使用 Anthropic `/v1/messages` 端点和 `x-api-key`。

多个服务商的密钥变量会在首次初始化时创建，但每次配置只把一个服务商写入：

```text
shortx_ai_enabled_count = 1
```

未使用的 Key 保持空值，也不会进入 HTTP 请求。切换服务商时重新输入完整配置和对应 Key。

## 回合制会话

- 输入普通消息：继续当前会话。
- 输入 `/new` 或 `/reset`：清空当前会话。
- 选择“查看历史会话”：显示当前本机保存的历史上下文。
- AI 收到的约束要求其读取私有 `shortx-rule-creator/SKILL.md` 和 references，并按该规范生成 ShortX DirectAction/Rule。
- 删除一键指令或自动指令时，会通过 `actionsOnDeleted` 清理配置变量、会话变量和所有服务商 Key 变量。

## 重要限制

这些限制来自当前 `shortx-rule-creator` 参考中公开的 ShortX 动作能力，不能把它们包装成已完成的功能：

- `DownloadFile` 可以下载仓库 ZIP，但公开动作没有可靠、通用的“解压 ZIP + 递归读取目录并把全部 Markdown 注入模型上下文”的组合动作。因此导入后需要手动把 `skills/` 解压到私有目录；规则会把该目录路径加入约束，但不能证明运行时确实读取了全部文件。
- ShortX 的 `HttpRequest` 参考只描述普通 HTTP 响应适配，没有 SSE/HTTP chunk 的流式输出动作。因此当前实现是“提交一回合、等待完整响应、显示完整回复”，不是 token 级流式输出。
- 当前会话历史保存在 ShortX 隐私全局变量中。规则没有可验证的 AES/Android Keystore 加密 API，因此不能声称已经实现密码学加密；如 ShortX 版本没有对 `isSecret` 全局变量提供加密存储，历史仍可能是普通本地变量存储。
- 会话上下文没有自动读取各模型服务商的上下文窗口元数据，也没有自动按 token 计数截断；`max_tokens`/`max_output_tokens` 当前是固定的 4096，使用超长历史时需要手动新建会话或后续扩展。
- OpenAI Responses 的 JSONPath 表达式、不同兼容服务商的模型名称和响应结构可能变化。导入后必须用实际服务商文档和真机请求验证。
- 本地验证只检查文件结构、JSON、分隔符、组件 ID 和密钥泄露，不等同于 ShortX 真机运行验证。

不要把真实 Key 写入 Git、规则文件、截图、聊天消息或仓库文档。