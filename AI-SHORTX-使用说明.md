# ShortX AI 一键指令与自动指令

本仓库新增了三份可导入的 ShortX 文本文件，以及供指令下载的 skills 压缩包：

- `da/ShortX-AI首次初始化与密钥设置.txt`
- `da/ShortX-AI回合制会话与模型切换.txt`
- `rule/ShortX-AI回合制会话自动指令.txt`
- `skills/shortx-rule-creator.zip`

## 导入顺序

1. 导入并运行 `ShortX-AI首次初始化与密钥设置.txt`。
2. 首次运行会显示使用说明链接：

   `https://github.com/snowzlmbot/ShortX-Files/blob/main/AI-SHORTX-%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E.md`

   必须等待 5 秒倒计时结束后，再确认并输入：

   ```text
   provider|model|protocol|完整请求URL|keyVariableName|skills私有目录
   ```

   默认示例：

   ```text
   OpenAI|gpt-5|openai_responses|https://api.openai.com/v1/responses|shortx_key_openai|/data/data/com.shortx/files/skills
   ```

3. 输入当前服务商 API Key。Key 只写入对应的 ShortX 隐私全局变量。
4. 初始化指令会下载：

   `https://raw.githubusercontent.com/snowzlmbot/ShortX-Files/main/skills/shortx-rule-creator.zip`

5. 初始化指令随后使用受限 `ShellCommand` 调用设备的 `unzip`，自动解压到填写的 ShortX 私有目录；不再需要手动解压。

   目标目录结构：

   ```text
   <skills私有目录>/shortx-rule-creator/SKILL.md
   <skills私有目录>/shortx-rule-creator/references/*.md
   ```

6. 导入并启用 `ShortX-AI回合制会话自动指令.txt`，把它绑定到 ShortX 磁贴 1。
7. 导入 `ShortX-AI回合制会话与模型切换.txt`。输入消息后，该一键指令保存本回合；点击磁贴 1 发送请求并显示回复。

## skills 压缩包

压缩包固定放在：

```text
skills/shortx-rule-creator.zip
```

压缩包内容为 `skills/shortx-rule-creator/` 及其全部 references，初始化动作会检查目标目录并替换旧版本目录。压缩包不包含脚本、密钥或符号链接。

### skills/shortx-rule-creator.zip

压缩包由 GitHub Actions 从 `skills/shortx-rule-creator/` 自动生成，固定下载地址为：

```text
https://raw.githubusercontent.com/snowzlmbot/ShortX-Files/main/skills/shortx-rule-creator.zip
```

## 支持的协议分支

- `openai_responses`：使用完整 `/responses` 端点，默认配置为 OpenAI。
- `openai_chat`：使用 OpenAI-compatible `/chat/completions` 端点。
- `anthropic_messages`：使用 Anthropic `/v1/messages` 端点和 `x-api-key`。

多个服务商的密钥变量会在首次初始化时创建，但每次配置只把一个服务商写入：

```text
shortx_ai_enabled_count = 1
```

未使用的 Key 保持空值，也不会进入 HTTP 请求。

## 回合制会话

- 输入普通消息：继续当前会话。
- 输入 `/new` 或 `/reset`：清空当前会话。
- 选择“查看历史会话”：显示当前本机保存的历史上下文。
- AI 收到的约束要求其读取私有 `shortx-rule-creator/SKILL.md` 和 references，并按该规范生成 ShortX DirectAction/Rule。
- 删除一键指令或自动指令时，会通过 `actionsOnDeleted` 清理配置变量、会话变量和所有服务商 Key 变量。

## 生成器兼容性

当前仓库生成器会递归读取 `da/`、`rule/` 和 `code/` 下的全部文件，并交给 ShortX 解析器；因此这些目录只能放有效的 ShortX 分享文件。说明文档和压缩包应放在目录外。

## 重要限制

- `unzip` 必须存在于 Android 设备环境中；如果设备没有该命令，初始化会在解压动作处失败并显示错误。压缩包会解压为 `目标目录/shortx-rule-creator/SKILL.md` 与 `目标目录/shortx-rule-creator/references/`，规则不会执行 ZIP 内脚本。
- `WriteGlobalVar` 的 `autoCreateIfMissing` 不是当前 ShortX `core-api.jar` 支持的字段；写入前应通过 `CreateGlobalVar` 创建变量，或删除该字段。
- ShortX 的 `HttpRequest` 参考只描述普通 HTTP 响应适配，没有 SSE/HTTP chunk 的流式输出动作。因此当前实现是“提交一回合、等待完整响应、显示完整回复”，不是 token 级流式输出。
- 当前会话历史保存在 ShortX 隐私全局变量中。规则没有可验证的 AES/Android Keystore 加密 API，因此不能声称已经实现密码学加密。
- 会话上下文没有自动读取各模型服务商的上下文窗口元数据，也没有自动按 token 计数截断；输出上限当前固定为 4096。
- 本地验证只检查文件结构、JSON、分隔符、组件 ID、ZIP 内容和密钥泄露，不等同于 ShortX 真机运行验证。

不要把真实 Key 写入 Git、规则文件、截图、聊天消息或仓库文档。
