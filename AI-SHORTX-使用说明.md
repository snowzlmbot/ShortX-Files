# ShortX AI 一键指令与自动指令

本仓库新增了三份可导入的 ShortX 文本文件，以及供指令下载的 skills 压缩包：

- `da/ShortX-AI首次初始化与密钥设置.txt`
- `da/ShortX-AI回合制会话与模型切换.txt`
- `rule/ShortX-AI回合制会话自动指令.txt`
- `skills/shortx-rule-creator.zip`

## 本地 AI Agent 指令

另外提供一组用于 root Android 本机本地 AI Agent 的 DirectAction：

- `da/ShortX-AI生成指令首次环境初始化.txt`
- `da/ShortX-启动AI指令生成.txt`
- `da/ShortX-结束AI指令生成.txt`
- `app/server.py`
- `app/configure_model.py`
- `app/env-key-put`
- `app/model.json`

初始化 DirectAction 会把本地服务资源和 `shortx-rule-creator` skill 安装到 `/data/local/ai-agent/`，启动 DirectAction 只绑定 `127.0.0.1`，停止 DirectAction 按 PID 文件优雅停止并保留会话/配置。

### 本地 Agent 的 API Key

API Key 不写入 `model.json`、Shell 参数、日志或会话；本地服务从 root-only 文件读取：

```text
/data/local/ai-agent/config/agent.env
```

文件格式由 `env-key-put` 写入：

```text
AI_AGENT_API_KEY_B64=<base64 编码的 Key>
```

文件权限必须为 `600`。当前实现没有伪称接入 Android Keystore；若设备要使用 Keystore，需要将 `env-key-put` 替换为经过信任验证的 Keystore 桥接程序。

本地服务支持：

- `GET /health`
- `GET /models`
- `GET /sessions`
- `GET /sessions/<id>`
- `POST /sessions`
- `POST /config`
- `POST /chat`，SSE 流式输出

支持协议：`openai_responses`、`openai_chat`、`anthropic_messages`。模型服务配置只保存 provider、model、协议、HTTPS endpoint 和 `AI_AGENT_API_KEY` 环境变量名；单次只启用一个 provider。

## 导入顺序

1. 导入并运行 `ShortX-AI首次初始化与密钥设置.txt`。
2. 首次运行会显示使用说明链接；必须等待 5 秒倒计时结束后确认。
3. 输入自定义服务商配置：

   ```text
   Custom|your-model|openai_responses|https://your-provider.example/v1/responses|shortx_key_custom|/data/data/com.shortx/files/skills
   ```

4. 输入当前服务商 API Key。Key 只写入对应的 ShortX 隐私全局变量。
5. 导入并启用 `ShortX-AI回合制会话自动指令.txt`，把它绑定到 ShortX 磁贴 1。
6. 导入 `ShortX-AI回合制会话与模型切换.txt`。输入消息后，点击磁贴 1 发送请求并显示回复。
7. 要使用本地 Agent，先导入并运行 `ShortX-AI生成指令首次环境初始化.txt`，再运行 `ShortX-启动AI指令生成.txt`。

## skills 压缩包

固定下载地址：

```text
https://raw.githubusercontent.com/snowzlmbot/ShortX-Files/main/skills/shortx-rule-creator.zip
```

压缩包内容为 `shortx-rule-creator/SKILL.md` 和 `shortx-rule-creator/references/`，初始化会将其解压到 `<skills私有目录>/shortx-rule-creator/`。

## 重要限制

- root Android 设备必须提供 `curl`、`unzip`、`python3` 和 `openssl`；本仓库不伪造或静默部署缺失运行时。
- Android Keystore 没有可验证的通用 ShortX 动作接口；本地 Agent 使用 root-only `agent.env`，不是 Keystore 存储。
- SSE、真实模型请求和会话加密由 `/data/local/ai-agent/app/server.py` 提供，不是 ShortX 原生 HTTP 动作提供。
- 本地服务只监听 loopback；不要把端口暴露到局域网或公网。
- 本地结构、单元测试和 HTTP smoke test 不等同于真实 Android root 设备、模型服务商和 ROM 测试。
