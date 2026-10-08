"""三模式框架：统一接口 + 自动路由。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Reply:
    """一次回答。solver 模式会填 hints；general 填 sources。"""

    text: str = ""
    mode: str = ""
    hints: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)


class Mode:
    """模式基类。子类实现 handle()。"""

    name = ""
    aliases = []

    def handle(self, message, images, context) -> Reply:
        raise NotImplementedError


class ModeRouter:
    """根据消息内容把请求分派到模式。

    显式 mode 优先；否则关键词打分；默认 general。
    """

    def __init__(self, modes):
        self.modes = {m.name: m for m in modes}
        # 中文关键词 → 模式
        self.keywords = {
            "solver": ["解题", "怎么算", "这道题", "求证", "方程", "计算",
                       "证明", "求解", "答案", "步骤", "几何", "函数",
                       "推导", "算一下", "多少"],
            "general": ["什么是", "是什么", "是多少", "为什么", "是谁", "哪一年", "介绍一下", "百科", "历史", "定义"],
            "companion": ["累", "烦", "焦虑", "坚持", "加油", "鼓励", "压力",
                          "拖延", "不想学", "考砸", "难过", "迷茫", "陪着",
                          "聊", "说说", "坚持不下去"],
        }

    def detect(self, message: str) -> str:
        scores = {}
        for mode_name in self.keywords.keys():
            kws = self.keywords[mode_name]
            hit = 0
            for kw in kws:
                if message.count(kw) > 0:
                    hit += 1
            if hit > 0:
                scores[mode_name] = hit
        if not scores:
            return "general"
        ranked = sorted(scores.keys(), key=scores.get, reverse=True)
        if len(ranked) > 1 and scores[ranked[0]] == scores[ranked[1]] and "general" in scores:
            return "general"
        return ranked[0]

    def route(self, message: str, images: list, mode: str, context) -> Reply:
        target = mode if self.modes.get(mode) else None
        if target is None:
            target = self.detect(message)
            solver = self.modes.get("solver")
            if target != "solver" and solver is not None:
                try:
                    if solver.can_parse(message):
                        target = "solver"
                except Exception:
                    pass
        chosen = self.modes.get(target, self.modes["general"])
        return chosen.handle(message, images, context)


