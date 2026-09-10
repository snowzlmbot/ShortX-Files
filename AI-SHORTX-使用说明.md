# ShortX AI 一键指令与自动指令使用说明

本目录中的三个新文件配合使用：

- `da/ShortX-AI首次初始化与密钥设置.txt`
  - 首次创建 10 个服务商独立的隐私全局变量；
  - 初始化当前唯一启用的服务商、模型、协议、官方完整请求端点；
  - 首次要求填写 API Key，并写入选定的隐私全局变量；
  - 下载 `https://github.com/snowzlmbot/ShortX-Files/archive/refs/heads/main.zip` 到 ShortX 可用的应用私有位置；
  - 删除该一键指令时清理服务商 Key、配置与会话变量。
- `da/ShortX-AI回合制会话与模型切换.txt`
  - 开始/继续会话、切换唯一启用的服务商/模型、查看状态、查看历史；
  - 每一回合把用户消息与历史拼成请求，供会话 Rule 调用当前唯一启用配置；
  - 删除该一键指令时清理本机 AI 配置、历史和全部服务商 Key 变量。
- `rule/ShortX-AI回合制会话自动指令.txt`
  - ShortX 磁贴 1 触发一回合交互；
  - 每回合先把固定安全约束、skills 私有目录路径、历史和用户消息拼成 prompt；
  - 按协议分支调用 OpenAI Responses、OpenAI Chat Completions 或 Anthropic Messages；
  - 用 JSONPath 提取文本结果，并保存历史与最近回复；
  - 删除该 Rule 时清理全部配置和服务商 Key。

## 首次导入顺序

1. 在 ShortX 导入并运行 `ShortX-AI首次初始化与密钥设置.txt`。
2. 只填写计划使用的一个服务商 Key；其他隐私全局变量保持空且不启用。
3. 从 GitHub 下载 `main.zip`，解压 `skills/` 到你填写的 ShortX 应用私有目录；确认目录中至少有：
   - `shortx-rule-creator/SKILL.md`
   - `shortx-rule-creator/references/actions.md`
   - `shortx-rule-creator/references/conditions.md`
   - `shortx-rule-creator/references/triggers.md`
   - `shortx-rule-creator/references/variables.md`
   - `shortx-rule-creator/references/advanced.md`
   - `shortx-rule-creator/references/examples.md`
4. 导入并启用 `ShortX-AI回合制会话自动指令.txt`。
5. 导入 `ShortX-AI回合制会话与模型切换.txt`，通过它开始会话或切换配置。
6. 在 ShortX 将 Rule 绑定到磁贴 1，点击磁贴触发一回合。

## 配置格式

切换或首次初始化时输入五段配置：

```text
provider|model|protocol|完整请求URL|keyVariableName
```

协议只能是：

- `openai_responses`
- `openai_chat`
- `anthropic_messages`

默认配置为：

```text
OpenAI|gpt-5|openai_responses|https://api.openai.com/v1/responses|shortx_key_openai
```

支持的预设模板包括 OpenAI、Anthropic、Google Gemini、xAI、DeepSeek、Mistral、Groq、Together AI 和 OpenRouter。预设只是模板；必须以各服务商当前官方文档中的模型、端点和协议为准。切换后仍只允许一个 `keyVariableName` 处于当前启用配置中。

## 交互方式

- 启动一键指令，选择“开始/继续会话”，输入一回合消息；
- 点击磁贴 1，Rule 会读取本机保存的 `shortx_ai_history`，向当前服务商发送一回合请求，并显示结果；
- 下一次再输入消息即可继续微调；
- `/new` 或 `/reset` 会清空当前历史；
- “从历史会话进入”会显示当前本机历史上下文；
- 当前版本按完整 HTTP 响应完成后显示回复，不是真正 token 级流式输出。

## 重要限制与真实能力边界

- ShortX 公开动作参考中没有通用的“递归读取目录、解压 ZIP、AES 加密会话、流式 HTTP 分块输出”动作。因此规则提供了下载和本机私有变量流程，但不能诚实地宣称已经完成递归 skills 读取、真正 AES 加密存储或 token 级流式输出。
- 规则会把 skills 私有目录路径和远程来源写入 prompt，要求会话模型使用该目录中的 `SKILL.md` 与 references；ShortX 动作本身不会替代模型执行真实目录递归读取。如果当前 ShortX 版本没有文件读取/解压/脚本能力，需要手动完成第 3 步。
- 当前规则通过 HTTP 请求实现单回合请求；JSONPath 只提取当前示例响应路径。不同服务商可能需要根据实际响应结构微调 JSONPath。
- 规则不会把任何真实 API Key 写入导出的文件；Key 只在首次运行时通过输入框写入对应的 `isSecret: true` 隐私全局变量。
- 删除钩子已配置清理各服务商 Key 与会话变量，但导入后请在 ShortX 中确认当前版本确实执行 `actionsOnDeleted`；如版本不支持该钩子，请先手动删除这些隐私全局变量。
- 本地结构验证不等同于 Android 真机、ShortX 版本、网络、权限或具体供应商 API 的运行验证。
- OpenAI Responses、Anthropic Messages、OpenAI-compatible 端点的实际字段与模型可用性可能变化，使用前需核对官方文档。
