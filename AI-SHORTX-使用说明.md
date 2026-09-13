# ShortX AI Web 引擎云端指令

本目录已移除旧版“ShortX AI 回合制会话”三份原生规则。现在统一使用 `ai-web-engine` 提供的本地 Web 引擎，ShortX 只负责从云端拉取最新脚本并执行。

## 最新三条指令

- `da/ShortX-AI生成指令首次环境初始化.txt`
- `da/ShortX-启动AI指令生成.txt`
- `da/ShortX-结束AI指令生成.txt`

三条指令的源代码位于公开仓库：

- <https://github.com/snowzlmbot/ai-web-engine/tree/main/shortx>

三条指令会通过 Raw 地址获取对应脚本：

```text
https://raw.githubusercontent.com/snowzlmbot/ai-web-engine/main/scripts/init.sh
https://raw.githubusercontent.com/snowzlmbot/ai-web-engine/main/scripts/start.sh
https://raw.githubusercontent.com/snowzlmbot/ai-web-engine/main/scripts/stop.sh
```

## 使用顺序

1. 导入并运行 `ShortX-AI生成指令首次环境初始化.txt`。
2. 初始化脚本会在 Android Root 设备创建 `/data/local/ai-instruction/`，按设备 ABI 自动下载对应 Release 二进制和 skills；支持 `arm64-v8a`、`armeabi-v7a`、`x86_64`、`x86`，不会覆盖 `config/model_config.json`、`config/master.key` 或 `sessions/`。
3. 在 ShortX 环境变量中设置：

   ```text
   模型key
   ```

4. 导入并运行 `ShortX-启动AI指令生成.txt`。该指令将 `%模型key%` 注入为 `AI_WEB_ENGINE_API_KEY`，然后启动 `127.0.0.1:6688`。
5. 浏览器访问：

   ```text
   http://127.0.0.1:6688
   ```

   首次打开如果右上角显示“需要配置”，这是正常的首次配置状态，不是连接失败。页面会自动打开“模型服务设置”。填写服务商、HTTPS 端点、协议、默认模型 ID 和模型列表后，点击“保存并连接”；状态变为“已连接”后，底部输入框和“发送”按钮会启用。

6. 使用 `ShortX-结束AI指令生成.txt` 停止引擎。停止脚本只操作自身 PID 文件对应的引擎进程，不使用宽泛 `pkill -f`，也不删除配置、密钥、会话、skills 或日志。

使用 `http://127.0.0.1:6688`，因为 Chromium/Chrome 会将 `6666` 判定为危险端口并返回 `ERR_UNSAFE_PORT`。

## 引擎能力

- OpenAI Chat Completions 和 Responses 协议；
- Anthropic Messages 协议；
- SSE 流式输出；
- 模型切换；
- 推理等级切换；
- 新建和恢复历史会话；
- AES-256-GCM 会话文件加密；
- 自动加载 `shortx-rule-creator/SKILL.md` 和 references；
- Web UI 嵌入 Android 多架构 Go 二进制。

## 远端资源

- 仓库：<https://github.com/snowzlmbot/ai-web-engine>
- Release：<https://github.com/snowzlmbot/ai-web-engine/releases/tag/v1.1.2>
- 全架构引擎包：<https://github.com/snowzlmbot/ai-web-engine/releases/download/v1.1.2/ai-web-engine-android-all.zip>
- ARM64 二进制：<https://github.com/snowzlmbot/ai-web-engine/releases/download/v1.1.2/ai-web-engine-android-arm64>
- 适配 skill：<https://raw.githubusercontent.com/snowzlmbot/ShortX-Files/main/skills/shortx-rule-creator.zip>

## 说明

此文档和三条指令是公开资源，不包含真实 API Key。环境变量 `模型key` 只在设备端展开并传给本地进程，不应写入仓库、日志、截图或会话。