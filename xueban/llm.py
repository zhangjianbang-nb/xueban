"""可选 LLM 客户端：OpenAI 兼容 /chat/completions，支持视觉。

零 SDK 依赖（urllib）。未配置时各模式走确定性引擎。
"""

from __future__ import annotations

import json
import urllib.request


class LLM:
    """OpenAI 兼容聊天客户端（chat.completions + 视觉 content parts）。"""

    def __init__(self, base_url, api_key="EMPTY", model="default", temp=0.3):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temp = temp

    def chat(self, messages, json_mode=False):
        """发消息，返回 assistant message dict。messages 已是 OpenAI 格式。"""
        payload = {"model": self.model, "messages": messages,
                   "temperature": self.temp}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + self.api_key})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]


class MockLLM(LLM):
    """测试用伪 LLM：按预设脚本依次返回，不发网络请求。

    script 项可为 dict（原样返回）或 callable(messages)->dict。
    """

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.base_url = "http://mock.local"
        self.model = "mock"

    def chat(self, messages, json_mode=False):
        self.calls.append(messages)
        item = self.script.pop(0)
        return item(messages) if callable(item) else item
