# ShortX AI 一键指令与自动指令使用说明

本目录中的三个新文件配合使用：

- `da/ShortX-AI首次初始化与密钥设置.txt`
  - 首次创建 10 个服务商独立的隐私全局变量；
  - 初始化当前唯一启用的服务商、模型、协议、官方完整请求端点；
  - 首次要求填写 API Key，并写入选定的隐私全局变量；
  - 下载 `https://github.com/snowzlmbot/ShortX-Files/archive/refs/heads/main.zip` 到 ShortX 可用的应用私有位置；
  - 停止该一键指令时清理会话运行变量；删除该一键指令时清理服务商 Key、配置与会话变量。
- `da/ShortX-AI回合制会话与模型切换.txt`
  - 开始/继续会话、切换唯一启用的服务商/模型、查看状态、清空会话；
  - `/new`、`/reset` 新会话；`/history` 显示历史；
  - 每一回合把用户消息与历史拼成请求，调用当前唯一启用配置；
  - 删除该一键指令时清理本机 AI 配置、历史和全部服务商 Key 变量。
- `rule/ShortX-AI回合制会话自动指令.txt`
  - ShortX 磁贴 1 触发一回合交互；
  - 每回合先拼装固定安全约束、远程 skills 地址说明、历史和用户消息；
  - 按协议分支调用 OpenAI Responses、OpenAI Chat Completions 或 Anthropic Messages；
  - 用 JSONPath 提取文本结果，并保存历史与最近回复；
  - 首次启用时提示下载/保存远程 skills 压缩包；删除该 Rule 时清理全部配置和服务商 Key。

## 首次导入顺序

1. 在 ShortX 导入并运行 `ShortX-AI首次初始化与密钥设置.txt`。
2. 只填写计划使用的一个服务商 Key；其他隐私全局变量保持空且不启用。
3. 导入并启用 `ShortX-AI回合制会话自动指令.txt`。
4. 导入 `ShortX-AI回合制会话与模型切换.txt`，通过它开始会话或切换配置。
5. 在 ShortX 配置磁贴 1，点击磁贴触发 Rule。

## 配置格式

切换时输入：

```text
provider|model|protocol|完整请求URL
```

协议只能是：

- `openai_responses`
- `openai_chat`
- `anthropic_messages`

默认配置为：

```text
OpenAI|gpt-5|openai_responses|https://api.openai.com/v1/responses
```

支持的预设模板包括 OpenAI、Anthropic、Google Gemini、xAI、DeepSeek、Mistral、Groq、Together AI 和 OpenRouter。预设只是模板；必须以各服务商当前官方文档中的模型、端点和协议为准。

## 重要限制

- ShortX 公开动作参考中没有通用的“递归读取目录、解压 ZIP、AES 加密会话、流式 HTTP 分块输出”动作。因此规则提供了下载和本机全局变量流程，但不能诚实地宣称已经完成递归 skills 读取、真正加密存储或 token 级流式输出。
- 当前规则通过 HTTP 请求实现单回合请求；完整响应正文通过 JSONPath 提取。不同服务商仍可能需要按其实际响应结构微调 JSONPath。
- 规则不会把任何真实 API Key 写入导出的文件；Key 只在首次运行时通过输入框写入对应的隐私全局变量。
- 删除钩子已配置清理各服务商 Key 与会话变量，但导入后请在 ShortX 中确认当前版本确实执行 `actionsOnDeleted`；如版本不支持该钩子，请先手动删除这些隐私全局变量。
- 本地结构验证不等同于 Android 真机、ShortX 版本、网络、权限或具体供应商 API 的运行验证。
- OpenAI Responses、Anthropic Messages、OpenAI-compatible 端点的实际字段与模型可用性可能变化，使用前需核对官方文档。
