"""XueBan 主类：模式路由 + 可选 LLM + 学生上下文。"""

from __future__ import annotations

from .image import ImageAttachment
from .modes import ModeRouter, Reply
from .modes_impl import CompanionMode, GeneralMode, SolverMode


class StudentContext:
    """学生状态：连续学习天数等（内存版，可持久化扩展）。"""

    def __init__(self, streak_days: int = 0):
        self._data = {"streak_days": streak_days}
        self.events = []

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def note_event(self, kind: str, detail: str = ""):
        self.events.append({"kind": kind, "detail": detail})

    def tick_streak(self) -> int:
        cur = self._data.get("streak_days", 0) + 1
        self._data["streak_days"] = cur
        return cur


class XueBan:
    """学伴智能体。

    参数:
        llm: llm.LLM 实例（可选）；None 时全部模式走离线引擎。
        context: StudentContext；缺省新建（streak 从 0 起）。
    """

    def __init__(self, llm=None, context=None):
        self.llm = llm
        self.context = context if context is not None else StudentContext()
        modes = [CompanionMode(), SolverMode(), GeneralMode()]
        self.router = ModeRouter(modes)

    def run(self, message: str, mode: str = "auto",
            images: list | None = None) -> Reply:
        """处理一条消息。mode: auto/companion/solver/general。"""
        imgs = []
        for spec in images or []:
            if isinstance(spec, ImageAttachment):
                imgs.append(spec)
            else:
                from .image import load_image
                imgs.append(load_image(spec))

        actual_mode = mode if mode != "auto" else ""
        if self.llm is not None:
            try:
                return self._run_llm(message, imgs, actual_mode)
            except Exception:
                pass  # 降级离线
        return self.router.route(message, imgs, actual_mode, self.context)

    def _run_llm(self, message: str, images: list, mode_hint: str) -> Reply:
        content_parts = [{"type": "text", "text": message}]
        for img in images:
            content_parts.append(img.to_openai_part())
        payload_msg = {"role": "user",
                       "content": content_parts if images else message}
        system = (
            "你是学生学伴，三种模式：陪伴（情绪支持不越界）、解题（先给提示阶梯"
            "再详解，绝不直接甩答案）、通识（回答附来源）。按问题性质自动选择。"
        )
        messages = [{"role": "system", "content": system}, payload_msg]
        answer = self.llm.chat(messages)
        if isinstance(answer, dict):
            text = answer.get("content", "")
        else:
            text = answer.content
        detected = self.router.detect(message) if not mode_hint else mode_hint
        reply = Reply(text=text, mode=detected or "general")
        reply.meta["engine"] = "llm"
        return reply
