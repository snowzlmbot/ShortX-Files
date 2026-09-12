#!/usr/bin/env python3
"""Loopback-only ShortX local AI agent.

The service reads model metadata from ``config/model.json`` and API keys from a
root-only environment file. API keys never appear in the configuration JSON,
sessions, HTTP responses, or logs. Sessions use OpenSSL AES-256-CTR plus an
HMAC-SHA256 integrity tag and stay under the local agent directory.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator
from urllib import error, request
from urllib.parse import urlparse

BASE = Path(os.environ.get("AI_AGENT_BASE", "/data/local/ai-agent"))
PORT = int(os.environ.get("AI_AGENT_PORT", "6666"))
SKILL_DIR = Path(os.environ.get("AI_AGENT_SKILL_DIR", str(BASE / "skills" / "shortx-rule-creator")))
CONFIG_PATH = Path(os.environ.get("AI_AGENT_MODEL_CONFIG", str(BASE / "config" / "model.json")))
ENV_PATH = Path(os.environ.get("AI_AGENT_ENV_FILE", str(BASE / "config" / "agent.env")))
SESSION_DIR = BASE / "sessions"
SESSION_KEY_PATH = BASE / "config" / "session.key"
MAX_BODY = 1_000_000
MAX_SESSION_MESSAGES = 80

DEFAULT_CONFIG: dict[str, Any] = {
    "active_provider": "custom",
    "providers": {
        "custom": {
            "enabled": True,
            "protocol": "openai_responses",
            "endpoint": "https://example.invalid/v1/responses",
            "model": "replace-with-model-id",
            "api_key_env": "AI_AGENT_API_KEY",
            "context_messages": 20,
        }
    },
    "reasoning_profiles": {
        "fast": {"label": "快速", "effort": "low", "max_output_tokens": 1024},
        "balanced": {"label": "平衡", "effort": "medium", "max_output_tokens": 2048},
        "deep": {"label": "深度思考", "effort": "high", "max_output_tokens": 4096},
    },
    "active_reasoning_profile": "balanced",
}

INDEX_HTML = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ShortX Local Agent</title>
<style>
:root{color-scheme:dark;--ink:#edf2f4;--muted:#9eb3bf;--edge:#2d414d;--bg:#0a1115;--pane:#101b22;--soft:#14252b;--a:#56d7b5;--u:#183f38}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px ui-sans-serif,system-ui,sans-serif}header{height:58px;display:flex;align-items:center;justify-content:space-between;padding:0 18px;border-bottom:1px solid var(--edge)}h1{margin:0;font-size:15px;letter-spacing:.04em}.online{font-size:12px;color:var(--a)}main{display:grid;grid-template-columns:250px minmax(0,1fr);height:calc(100vh - 58px)}aside{padding:16px;border-right:1px solid var(--edge);overflow:auto}.btn,select,textarea,input{font:inherit;color:inherit;background:var(--pane);border:1px solid var(--edge);border-radius:5px}.btn{padding:8px 10px;cursor:pointer}.btn:hover{border-color:var(--a)}.session{display:block;text-align:left;width:100%;margin:6px 0;padding:8px 9px}.caption{font-size:11px;color:var(--muted);margin:18px 0 8px}.work{display:flex;flex-direction:column;min-width:0}.controls{display:flex;gap:9px;align-items:center;padding:10px 16px;border-bottom:1px solid var(--edge);flex-wrap:wrap}.controls label{font-size:11px;color:var(--muted)}select{padding:7px}.chat{flex:1;overflow:auto;width:min(980px,100%);margin:auto;padding:22px}.message{white-space:pre-wrap;border:1px solid var(--edge);border-radius:6px;padding:12px 14px;margin:12px 0;line-height:1.55}.user{background:var(--u);border-color:#28645a}.assistant{background:var(--pane)}.composer{width:min(980px,100%);margin:auto;border-top:1px solid var(--edge);display:flex;gap:10px;padding:14px}.composer textarea{min-height:74px;resize:vertical;flex:1;padding:10px}.hint{color:var(--muted);font-size:12px;line-height:1.55}.modal{position:fixed;inset:0;background:#000a;display:none;place-items:center}.modal.show{display:grid}.card{width:min(560px,92vw);padding:18px;background:var(--pane);border:1px solid var(--edge);border-radius:8px}.card input{width:100%;padding:8px;margin:6px 0 12px}.row{display:flex;gap:8px;justify-content:flex-end}@media(max-width:700px){main{grid-template-columns:1fr}aside{display:none}.chat{padding:14px}}
</style></head><body><header><h1>SHORTX LOCAL AGENT</h1><span id="status" class="online">检查中</span></header><main><aside><button id="new" class="btn">+ 新会话</button><div class="caption">历史会话</div><div id="sessions"></div><div class="caption">安全</div><p class="hint">仅监听 127.0.0.1。Key 通过受保护环境变量加载，不显示在页面或会话中。</p></aside><section class="work"><div class="controls"><label>服务商</label><select id="provider"></select><label>推理档位</label><select id="reasoning"></select><button id="config" class="btn">配置模型</button></div><div id="chat" class="chat"></div><form id="form" class="composer"><textarea id="input" placeholder="描述你要生成或微调的 ShortX Rule / DirectAction..."></textarea><button class="btn">发送</button></form></section></main><div id="modal" class="modal"><div class="card"><h2>配置模型服务</h2><label>服务商 ID</label><input id="cfgProvider" value="custom"><label>模型 ID</label><input id="cfgModel"><label>协议</label><select id="cfgProtocol"><option value="openai_responses">OpenAI Responses</option><option value="openai_chat">OpenAI Chat</option><option value="anthropic_messages">Anthropic Messages</option></select><label>完整请求端点</label><input id="cfgEndpoint"><label>API Key（仅写入受保护环境变量）</label><input id="cfgKey" type="password"><div class="row"><button id="cancel" class="btn">取消</button><button id="save" class="btn">保存</button></div></div></div><script>
let activeSession=null;const $=id=>document.getElementById(id);function msg(role,text){const e=document.createElement('div');e.className='message '+role;e.textContent=text;$('chat').appendChild(e);$('chat').scrollTop=$('chat').scrollHeight;return e}async function api(path,opt){const r=await fetch(path,opt);if(!r.ok)throw new Error(await r.text());return r}async function refresh(){const health=await api('/health').then(r=>r.json());$('status').textContent=health.ready?'就绪':'需要初始化';const data=await api('/models').then(r=>r.json());$('provider').innerHTML=data.providers.map(p=>`<option value="${p.id}">${p.id} · ${p.model}</option>`).join('');$('reasoning').innerHTML=data.reasoning.map(p=>`<option value="${p.id}">${p.label}</option>`).join('');const sessions=await api('/sessions').then(r=>r.json());$('sessions').innerHTML=sessions.sessions.map(s=>`<button class="btn session" data-id="${s.id}">${s.title||s.id}</button>`).join('');document.querySelectorAll('.session').forEach(x=>x.onclick=()=>openSession(x.dataset.id))}async function openSession(id){activeSession=id;const d=await api('/sessions/'+id).then(r=>r.json());$('chat').innerHTML='';d.messages.forEach(m=>msg(m.role,m.content))}function newSession(){activeSession=null;$('chat').innerHTML='';msg('assistant','新会话已就绪。描述需要生成的 ShortX 自动化。')}$('new').onclick=newSession;$('config').onclick=async()=>{const c=await api('/config').then(r=>r.json());const p=c.providers[$('provider').value]||{};$('cfgProvider').value=$('provider').value;$('cfgModel').value=p.model||'';$('cfgProtocol').value=p.protocol||'openai_responses';$('cfgEndpoint').value=p.endpoint||'';$('cfgKey').value='';$('modal').classList.add('show')};$('cancel').onclick=()=>{$('modal').classList.remove('show')};$('save').onclick=async()=>{try{await api('/config',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({provider:$('cfgProvider').value,model:$('cfgModel').value,protocol:$('cfgProtocol').value,endpoint:$('cfgEndpoint').value,api_key:$('cfgKey').value})});$('modal').classList.remove('show');await refresh()}catch(e){alert(e.message)}};$('form').onsubmit=async e=>{e.preventDefault();const text=$('input').value.trim();if(!text)return;$('input').value='';msg('user',text);const ai=msg('assistant','');try{const res=await api('/chat',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({session_id:activeSession,message:text,provider:$('provider').value,reasoning:$('reasoning').value})});const reader=res.body.getReader(),dec=new TextDecoder();let buf='';while(true){const n=await reader.read();if(n.done)break;buf+=dec.decode(n.value,{stream:true});const chunks=buf.split('\n\n');buf=chunks.pop();for(const chunk of chunks){for(const line of chunk.split('\n'))if(line.startsWith('data: ')){const d=JSON.parse(line.slice(6));if(d.session_id)activeSession=d.session_id;if(d.token)ai.textContent+=d.token;if(d.error)ai.textContent+='\n'+d.error}}}}catch(err){ai.textContent=err.message}await refresh()};refresh().catch(e=>{$('status').textContent='错误: '+e.message});newSession();
</script></body></html>"""


def config_dir() -> Path:
    return CONFIG_PATH.parent


def default_config() -> dict[str, Any]:
    return {
        "active_provider": "custom",
        "providers": {
            "custom": {
                "enabled": True,
                "protocol": "openai_responses",
                "endpoint": "https://example.invalid/v1/responses",
                "model": "replace-with-model-id",
                "api_key_env": "AI_AGENT_API_KEY",
                "context_messages": 20,
            }
        },
        "reasoning_profiles": {
            "fast": {"label": "快速", "effort": "low", "max_output_tokens": 1024},
            "balanced": {"label": "平衡", "effort": "medium", "max_output_tokens": 2048},
            "deep": {"label": "深度思考", "effort": "high", "max_output_tokens": 4096},
        },
        "active_reasoning_profile": "balanced",
        "listen_host": "127.0.0.1",
    }


def read_config() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        return default_config()
    config = json.loads(CONFIG_PATH.read_text())
    base = default_config()
    base.update(config)
    return base


def write_config(config: dict[str, Any]) -> None:
    config_dir().mkdir(parents=True, exist_ok=True)
    temp = CONFIG_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    os.chmod(temp, 0o600)
    temp.replace(CONFIG_PATH)


def load_environment() -> None:
    """Load only the local root-owned environment file into this process."""
    if not ENV_PATH.is_file():
        return
    if ENV_PATH.stat().st_mode & 0o077:
        raise RuntimeError("AI_AGENT_ENV_FILE must not be group/world accessible")
    for line in ENV_PATH.read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, encoded = line.split("=", 1)
        if name != "AI_AGENT_API_KEY_B64":
            continue
        os.environ["AI_AGENT_API_KEY"] = base64.b64decode(encoded.encode()).decode("utf-8")


def write_api_key_environment(api_key: str) -> None:
    if not api_key:
        return
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    value = base64.b64encode(api_key.encode("utf-8")).decode("ascii")
    temp = ENV_PATH.with_suffix(".tmp")
    temp.write_text("AI_AGENT_API_KEY_B64=" + value + "\n")
    os.chmod(temp, 0o600)
    temp.replace(ENV_PATH)
    os.environ["AI_AGENT_API_KEY"] = api_key


def session_secret() -> bytes:
    SESSION_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SESSION_KEY_PATH.exists():
        SESSION_KEY_PATH.write_text(secrets.token_hex(32) + "\n")
        os.chmod(SESSION_KEY_PATH, 0o600)
    if SESSION_KEY_PATH.stat().st_mode & 0o077:
        raise RuntimeError("session key must not be group/world accessible")
    return bytes.fromhex(SESSION_KEY_PATH.read_text().strip())


def _openssl(data: bytes, decrypt: bool = False) -> bytes:
    command = ["openssl", "enc", "-aes-256-ctr", "-pbkdf2", "-iter", "200000", "-salt", "-pass", f"file:{SESSION_KEY_PATH}"]
    if decrypt:
        command.append("-d")
    result = subprocess.run(command, input=data, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("OpenSSL session cipher failed")
    return result.stdout


def encrypt_session(data: bytes) -> str:
    secret = session_secret()
    ciphertext = _openssl(data)
    tag = hmac.new(secret, ciphertext, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(tag + ciphertext).decode("ascii")


def decrypt_session(value: str) -> bytes:
    packed = base64.urlsafe_b64decode(value.encode("ascii"))
    secret = session_secret()
    if len(packed) <= hashlib.sha256().digest_size:
        raise ValueError("invalid session envelope")
    tag, ciphertext = packed[:32], packed[32:]
    if not hmac.compare_digest(tag, hmac.new(secret, ciphertext, hashlib.sha256).digest()):
        raise ValueError("session integrity check failed")
    return _openssl(ciphertext, decrypt=True)


def session_path(session_id: str) -> Path:
    return SESSION_DIR / (hashlib.sha256(session_id.encode("utf-8")).hexdigest() + ".session")


def save_session(session_id: str, data: dict[str, Any]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    encoded = encrypt_session(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    target = session_path(session_id)
    temp = target.with_suffix(".tmp")
    temp.write_text(encoded)
    os.chmod(temp, 0o600)
    temp.replace(target)


def load_session(session_id: str) -> dict[str, Any]:
    return json.loads(decrypt_session(session_path(session_id).read_text()).decode("utf-8"))


def load_session_file(path: Path) -> dict[str, Any]:
    return json.loads(decrypt_session(path.read_text()).decode("utf-8"))


def relevant_reference_names(message: str) -> list[str]:
    lowered = message.lower()
    names = ["actions.md", "variables.md"]
    if any(token in message for token in ("触发", "通知", "屏幕", "应用", "定时", "手势", "按键")):
        names.append("triggers.md")
    if any(token in message for token in ("条件", "仅当", "如果", "判断")):
        names.append("conditions.md")
    if any(token in message for token in ("循环", "函数", "钩子", "退出", "参数")):
        names.append("advanced.md")
    if "example" in lowered or "示例" in message:
        names.append("examples.md")
    return list(dict.fromkeys(names))


def load_skill_context(message: str) -> str:
    skill = SKILL_DIR / "SKILL.md"
    refs = SKILL_DIR / "references"
    if not skill.is_file() or not refs.is_dir():
        raise RuntimeError("shortx-rule-creator skill is not installed")
    chunks = ["# Loaded shortx-rule-creator/SKILL.md", skill.read_text()]
    for name in relevant_reference_names(message):
        path = refs / name
        if path.is_file():
            chunks.extend([f"# Loaded reference: {name}", path.read_text()])
    return "\n\n".join(chunks)


def build_system_prompt(skill_context: str) -> str:
    return (
        "You are a ShortX instruction author. Follow the loaded shortx-rule-creator skill exactly. "
        "Use documented protobuf types/fields only. Produce an importable three-part ShortX file when asked for one: "
        "JSON, the literal separator ###------###, and a matching rule/da marker. "
        "Never execute user-provided shell, JavaScript, MVEL, network, or Android actions. "
        "Never request, reveal, or write API keys, credentials, cookies, or tokens.\n\n"
        + skill_context
    )


def trim_messages(messages: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    return messages[-max(2, min(limit, MAX_SESSION_MESSAGES)):]


def build_provider_request(provider: dict[str, Any], system: str, messages: list[dict[str, str]], reasoning: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    protocol = provider.get("protocol", "openai_responses")
    model = provider.get("model", "")
    api_key = os.environ.get(provider.get("api_key_env", "AI_AGENT_API_KEY"), "")
    if not api_key:
        raise RuntimeError("AI_AGENT_API_KEY is not configured")
    profile = {"max_output_tokens": int(reasoning.get("max_output_tokens", 2048)), "effort": reasoning.get("effort", "medium")}
    if protocol == "anthropic_messages":
        return ({"model": model, "system": system, "messages": messages, "stream": True, "max_tokens": profile["max_output_tokens"]}, {"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"})
    if protocol == "openai_chat":
        body: dict[str, Any] = {"model": model, "messages": [{"role": "system", "content": system}, *messages], "stream": True, "max_tokens": profile["max_output_tokens"]}
        body["reasoning_effort"] = profile["effort"]
        return body, {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
    if protocol == "openai_responses":
        body = {"model": model, "instructions": system, "input": messages, "stream": True, "max_output_tokens": profile["max_output_tokens"], "reasoning": {"effort": profile["effort"]}}
        return body, {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
    raise RuntimeError("unsupported provider protocol")


def extract_stream_token(protocol: str, event: dict[str, Any]) -> str:
    if protocol == "anthropic_messages":
        return str(event.get("delta", {}).get("text", ""))
    if protocol == "openai_chat":
        choices = event.get("choices", [])
        return str(choices[0].get("delta", {}).get("content", "")) if choices else ""
    if protocol == "openai_responses":
        return str(event.get("delta", event.get("output_text", "")))
    return ""


def provider_stream(provider: dict[str, Any], system: str, messages: list[dict[str, str]], reasoning: dict[str, Any]) -> Iterator[str]:
    body, headers = build_provider_request(provider, system, messages, reasoning)
    endpoint = str(provider.get("endpoint", ""))
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("provider endpoint must be an HTTPS URL")
    req = request.Request(endpoint, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=120) as response:
            for raw in response:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload in ("[DONE]", ""):
                    continue
                try:
                    token = extract_stream_token(str(provider.get("protocol")), json.loads(payload))
                except json.JSONDecodeError:
                    continue
                if token:
                    yield token
    except error.HTTPError as exc:
        raise RuntimeError(f"provider request failed: HTTP {exc.code}") from exc
    except error.URLError as exc:
        raise RuntimeError("provider request failed: network error") from exc


def public_config() -> dict[str, Any]:
    config = read_config()
    providers = {
        key: {field: value for field, value in value.items() if field != "api_key_env"}
        for key, value in config.get("providers", {}).items()
    }
    return {"active_provider": config.get("active_provider"), "providers": providers, "reasoning_profiles": config.get("reasoning_profiles", {})}


class Handler(BaseHTTPRequestHandler):
    server_version = "ShortXLocalAgent/1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def send_json(self, value: Any, status: int = 200) -> None:
        raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        if length <= 0 or length > MAX_BODY:
            raise ValueError("invalid request body")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise ValueError("request body must be an object")
        return value

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            raw = INDEX_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if path == "/health":
            skill_ready = (SKILL_DIR / "SKILL.md").is_file() and (SKILL_DIR / "references").is_dir()
            self.send_json({"ready": skill_ready and CONFIG_PATH.is_file(), "host": "127.0.0.1", "port": PORT, "skill_ready": skill_ready})
            return
        if path == "/models":
            config = read_config()
            providers = [{"id": key, "model": value.get("model", ""), "enabled": bool(value.get("enabled"))} for key, value in config.get("providers", {}).items()]
            reasoning = [{"id": key, "label": value.get("label", key)} for key, value in config.get("reasoning_profiles", {}).items()]
            self.send_json({"providers": providers, "reasoning": reasoning})
            return
        if path == "/config":
            self.send_json(public_config())
            return
        if path == "/sessions":
            rows: list[dict[str, Any]] = []
            if SESSION_DIR.is_dir():
                for candidate in SESSION_DIR.glob("*.session"):
                    try:
                        session = load_session_file(candidate)
                        rows.append({"id": session["id"], "title": session.get("title", ""), "updated_at": session.get("updated_at", 0)})
                    except Exception:
                        continue
            rows.sort(key=lambda item: item["updated_at"], reverse=True)
            self.send_json({"sessions": rows})
            return
        if path.startswith("/sessions/"):
            session_id = path.rsplit("/", 1)[-1]
            try:
                self.send_json(load_session(session_id))
            except Exception:
                self.send_json({"error": "session not found"}, 404)
            return
        self.send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = self.read_body()
        except Exception as exc:
            self.send_json({"error": str(exc)}, 400)
            return
        if path == "/config":
            self.update_config(body)
            return
        if path == "/chat":
            self.chat(body)
            return
        self.send_json({"error": "not found"}, 404)

    def update_config(self, body: dict[str, Any]) -> None:
        provider_id = str(body.get("provider", "custom")).strip()
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,48}", provider_id):
            self.send_json({"error": "invalid provider id"}, 400)
            return
        endpoint = str(body.get("endpoint", "")).strip()
        parsed = urlparse(endpoint)
        if parsed.scheme != "https" or not parsed.netloc:
            self.send_json({"error": "endpoint must be HTTPS"}, 400)
            return
        protocol = str(body.get("protocol", ""))
        if protocol not in {"openai_responses", "openai_chat", "anthropic_messages"}:
            self.send_json({"error": "unsupported protocol"}, 400)
            return
        model = str(body.get("model", "")).strip()
        if not model or len(model) > 160:
            self.send_json({"error": "invalid model"}, 400)
            return
        api_key = str(body.get("api_key", ""))
        if api_key:
            write_api_key_environment(api_key)
        config = read_config()
        providers = config.setdefault("providers", {})
        providers[provider_id] = {"enabled": True, "protocol": protocol, "endpoint": endpoint, "model": model, "api_key_env": "AI_AGENT_API_KEY", "context_messages": 20}
        for key, value in providers.items():
            value["enabled"] = key == provider_id
        config["active_provider"] = provider_id
        write_config(config)
        self.send_json({"ok": True, "provider": provider_id})

    def chat(self, body: dict[str, Any]) -> None:
        message = str(body.get("message", "")).strip()
        if not message or len(message) > 100_000:
            self.send_json({"error": "message required"}, 400)
            return
        config = read_config()
        provider_id = str(body.get("provider") or config.get("active_provider", "custom"))
        provider = config.get("providers", {}).get(provider_id)
        if not provider or not provider.get("enabled"):
            self.send_json({"error": "selected provider is not enabled"}, 400)
            return
        reasoning_id = str(body.get("reasoning") or config.get("active_reasoning_profile", "balanced"))
        reasoning = config.get("reasoning_profiles", {}).get(reasoning_id, {})
        session_id = str(body.get("session_id") or secrets.token_urlsafe(18))
        if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", session_id):
            self.send_json({"error": "invalid session id"}, 400)
            return
        try:
            session = load_session(session_id)
        except Exception:
            session = {"id": session_id, "title": message[:60], "messages": []}
        session["messages"].append({"role": "user", "content": message})
        messages = trim_messages(session["messages"], int(provider.get("context_messages", 20)))
        try:
            skill_context = load_skill_context(message)
            system = build_system_prompt(skill_context)
            load_environment()
            stream = provider_stream(provider, system, messages, reasoning)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            answer_parts: list[str] = []
            for token in stream:
                answer_parts.append(token)
                self.wfile.write(("data: " + json.dumps({"session_id": session_id, "token": token}, ensure_ascii=False) + "\n\n").encode("utf-8"))
                self.wfile.flush()
            answer = "".join(answer_parts)
            session["messages"].append({"role": "assistant", "content": answer})
            session["updated_at"] = int(time.time())
            save_session(session_id, session)
            self.wfile.write(("data: " + json.dumps({"session_id": session_id, "done": True}) + "\n\n").encode("utf-8"))
            self.wfile.flush()
        except Exception as exc:
            if not self.wfile.closed:
                try:
                    self.wfile.write(("data: " + json.dumps({"session_id": session_id, "error": str(exc)}) + "\n\n").encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    pass


def main() -> None:
    if not (SKILL_DIR / "SKILL.md").is_file():
        raise SystemExit("shortx-rule-creator skill is missing")
    if not (1024 <= PORT <= 65535):
        raise SystemExit("AI_AGENT_PORT must be between 1024 and 65535")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
