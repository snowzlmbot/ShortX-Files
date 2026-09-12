#!/usr/bin/env python3
"""Validate one model/provider line and write model.json atomically.

Input format: provider|model|protocol|https-endpoint
The API key is intentionally not accepted here; it belongs in agent.env.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

PROTOCOLS = {"openai_responses", "openai_chat", "anthropic_messages"}
PROVIDER_RE = re.compile(r"^[A-Za-z0-9_-]{1,48}$")


def main() -> int:
    base = Path(os.environ.get("AI_AGENT_BASE", "/data/local/ai-agent"))
    config_path = base / "config" / "model.json"
    raw = sys.stdin.read().strip()
    parts = [part.strip() for part in raw.split("|", 3)]
    if len(parts) != 4:
        print("expected provider|model|protocol|https-endpoint", file=sys.stderr)
        return 2
    provider, model, protocol, endpoint = parts
    if not PROVIDER_RE.fullmatch(provider) or not model:
        print("invalid provider or model", file=sys.stderr)
        return 2
    if protocol not in PROTOCOLS:
        print("unsupported protocol", file=sys.stderr)
        return 2
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        print("endpoint must be HTTPS", file=sys.stderr)
        return 2
    config = {
        "active_provider": provider,
        "providers": {
            provider: {
                "enabled": True,
                "protocol": protocol,
                "endpoint": endpoint,
                "model": model,
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
    config_path.parent.mkdir(parents=True, exist_ok=True)
    temp = config_path.with_suffix(".tmp")
    temp.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    os.chmod(temp, 0o600)
    temp.replace(config_path)
    print("model configuration saved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
