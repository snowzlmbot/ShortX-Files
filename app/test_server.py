#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from typing import Any, cast

spec = importlib.util.spec_from_file_location("shortx_agent", Path(__file__).with_name("server.py"))
assert spec and spec.loader
agent = cast(Any, importlib.util.module_from_spec(spec))
spec.loader.exec_module(agent)


class AgentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        agent.BASE = base
        agent.CONFIG_PATH = base / "config" / "model.json"
        agent.os.environ["AI_AGENT_API_KEY"] = "key"
        agent.SESSION_DIR = base / "sessions"
        agent.SESSION_KEY_PATH = base / "config" / "session.key"
        agent.SKILL_DIR = base / "skills" / "shortx-rule-creator"
        agent.SKILL_DIR.mkdir(parents=True)
        (agent.SKILL_DIR / "SKILL.md").write_text("# Skill\n")
        refs = agent.SKILL_DIR / "references"
        refs.mkdir()
        (refs / "actions.md").write_text("# Actions\n")
        (refs / "triggers.md").write_text("# Triggers\n")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_session_cipher_rejects_tampering(self) -> None:
        encrypted = agent.encrypt_session(b'{"hello":"world"}')
        self.assertEqual(agent.decrypt_session(encrypted), b'{"hello":"world"}')
        with self.assertRaises(ValueError):
            agent.decrypt_session(encrypted[:-2] + "AA")

    def test_provider_request_shapes(self) -> None:
        body, headers = agent.build_provider_request({"protocol": "openai_responses", "model": "gpt-test", "api_key_env": "AI_AGENT_API_KEY"}, "prompt", [{"role": "user", "content": "prompt"}], {"effort": "low", "max_output_tokens": 100})
        self.assertTrue(body["stream"])
        self.assertEqual(body["model"], "gpt-test")
        self.assertEqual(headers["Authorization"], "Bearer key")
        chat, _ = agent.build_provider_request({"protocol": "openai_chat", "model": "chat-test", "api_key_env": "AI_AGENT_API_KEY"}, "system", [{"role": "user", "content": "prompt"}], {})
        self.assertTrue(chat["stream"])
        anthropic, headers = agent.build_provider_request({"protocol": "anthropic_messages", "model": "claude-test", "api_key_env": "AI_AGENT_API_KEY"}, "system", [{"role": "user", "content": "prompt"}], {})
        self.assertTrue(anthropic["stream"])
        self.assertEqual(headers["x-api-key"], "key")

    def test_extract_stream_token(self) -> None:
        self.assertEqual(agent.extract_stream_token("openai_chat", {"choices": [{"delta": {"content": "hello"}}]}), "hello")
        self.assertEqual(agent.extract_stream_token("anthropic_messages", {"delta": {"text": "hello"}}), "hello")
        self.assertEqual(agent.extract_stream_token("openai_responses", {"delta": "hello"}), "hello")

    def test_skill_context(self) -> None:
        context = agent.load_skill_context("屏幕关闭时触发，并显示通知")
        self.assertIn("# Skill", context)
        self.assertIn("# Actions", context)
        self.assertIn("# Triggers", context)


if __name__ == "__main__":
    unittest.main()
