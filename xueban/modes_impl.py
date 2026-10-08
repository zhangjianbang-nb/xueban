"""三个具体模式：陪伴 / 解题 / 通识。

每个模式双路径：有 LLM 走模型（多模态图片走 vision），无 LLM 走
确定性引擎（离线可用、可测试）。
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from .modes import Mode, Reply


# ---------------------------------------------------------------- 陪伴模式
EMOTION_PATTERNS = [
    ("挫败", ["考砸", "不会", "学不会", "挫败", "崩溃", "做不到"]),
    ("疲惫", ["累", "熬夜", "困", "撑不住", "好累", "疲惫"]),
    ("焦虑", ["焦虑", "担心", "害怕", "来不及", "紧张", "压力大"]),
    ("拖延", ["拖延", "不想开始", "刷手机", "明再做", "明天再做", "静不下心"]),
    ("低落", ["难过", "沮丧", "emo", "委屈", "孤独", "难过"]),
]

RESPONSES = {
    "挫败": "一次没做好不代表不行，只是这道坎还没迈过去。我们把问题拆小一点：你现在卡在哪一步？说出来我陪你一起看。",
    "疲惫": "累了就先歇 10 分钟，学习不是比谁熬得狠。回来我们只做一件小事，做完就算赢。",
    "焦虑": "焦虑说明你在乎，但一次担心一件事就好。现在最让你担心的是哪一个？我们排个先后顺序。",
    "拖延": "不想开始很正常，那就把任务缩到 5 分钟版：只翻开书看一道题，5 分钟后想停就停。要不要现在试？",
    "低落": "听起来今天不太好受。情绪不用急着赶走，先陪它坐一会儿。想说说发生什么了吗？",
    "开心": "状态不错就趁热打铁，不过也记得喝水休息。今天打算推进哪科？",
    "中性": "我在呢。想聊会儿天、做道题，还是就随便说说？都行。",
}


class CompanionMode(Mode):
    """陪伴模式：情绪识别 + 回应 + 简单学习记录。"""

    name = "companion"
    aliases = ["陪伴", "聊天"]

    def handle(self, message, images, context) -> Reply:
        reply = Reply(mode=self.name)
        emotion = self._detect_emotion(message)
        reply.meta["emotion"] = emotion

        # 学习会话追踪（context 可持久化）
        if context is not None:
            context.note_event("companion", emotion)
            streak = context.get("streak_days", 0)
            if streak:
                reply.text = f"（你已连续学习 {streak} 天）\n" + RESPONSES.get(emotion, RESPONSES["中性"])
            else:
                reply.text = RESPONSES.get(emotion, RESPONSES["中性"])
        else:
            reply.text = RESPONSES.get(emotion, RESPONSES["中性"])
        return reply

    def _detect_emotion(self, message: str) -> str:
        for emotion, words in EMOTION_PATTERNS:
            for w in words:
                if message.count(w) > 0:
                    return emotion
        if message.count("开心") > 0 or message.count("不错") > 0 or message.count("爽") > 0:
            return "开心"
        return "中性"


# ---------------------------------------------------------------- 解题模式
class SolverMode(Mode):
    """解题模式：确定性解题器（方程/算术/百分比）+ 提示阶梯。

    设计原则：先给提示不直接给答案，学生要"再来一步"才升级到完整解答。
    """

    name = "solver"
    aliases = ["解题", "solver"]

    def handle(self, message, images, context) -> Reply:
        reply = Reply(mode=self.name)
        parsed = self._parse_problem(message)
        if parsed is None:
            reply.text = "目前离线解题器支持：一元一次方程（如 2x+3=7）、四则运算（如 12+3*4）、百分比（如 60 的 25%）。其他题型需要接入 LLM。"
            return reply
        kind, data = parsed
        try:
            if kind == "linear":
                reply.text, reply.hints = self._solve_linear(data)
            elif kind == "arith":
                reply.text, reply.hints = self._solve_arith(data)
            elif kind == "percent":
                reply.text, reply.hints = self._solve_percent(data)
        except Exception as exc:
            reply.text = "解析失败: " + str(exc)
        return reply

    def can_parse(self, message: str) -> bool:
        return self._parse_problem(message) is not None

    def _parse_problem(self, message: str):
        msg = message.replace("％", "%")
        m = re.search(r"([\d.]+)\s*的\s*([\d.]+)\s*%", msg)
        if m:
            return ("percent", (float(m.group(1)), float(m.group(2))))
        m = re.search(r"([\d.]+)\s*%\s*的\s*([\d.]+)", msg)
        if m:
            return ("percent", (float(m.group(2)), float(m.group(1))))
        m = re.search(r"(-?\d*)\s*x\s*([+-]\s*\d+)?\s*=\s*([\d.]+)", msg)
        if m:
            raw_a = m.group(1)
            a = -1.0 if raw_a == "-" else (1.0 if raw_a == "" else float(raw_a))
            b = float((m.group(2) or "+0").replace(" ", ""))
            c = float(m.group(3))
            return ("linear", (a, b, c))
        m = re.search(r"([\d.]+(?:\s*[+\-*/]\s*[\d.]+)+)", message)
        if m:
            return ("arith", m.group(1))
        return None

    def _solve_linear(self, abc):
        a, b, c = abc
        if a == 0:
            return "系数 a 为 0，不是有效的一元一次方程。", []
        x = (c - b) / a
        hints = [
            f"提示 1：把常数项移到右边：{self._fmt(a)}x = {self._fmt(c - b)}",
            f"提示 2：两边同除以 {self._fmt(a)}",
        ]
        text = f"x = {self._fmt(x)}"
        return text, hints

    def _solve_arith(self, expr: str):
        if not re.fullmatch(r"[\d.+\-*/() ]+", expr):
            return "表达式含不安全字符。", []
        val = eval(expr)  # noqa: S307 - 已白名单校验仅数字与运算符
        steps = f"先乘除后加减：{expr} = {self._fmt(val)}"
        return steps, ["提示：注意运算优先级，先算乘除除后算加减。"]

    def _solve_percent(self, pair):
        total, pct = pair
        val = total * pct / 100.0
        text = f"{self._fmt(total)} 的 {self._fmt(pct)}% = {self._fmt(total)} × {self._fmt(pct / 100.0)} = {self._fmt(val)}"
        return text, [f"提示：百分之几就是除以 100，{self._fmt(pct)}% = {self._fmt(pct / 100.0)}。"]

    @staticmethod
    def _fmt(v: float) -> str:
        if float(v).is_integer():
            return str(int(v))
        return f"{v:g}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- 通识模式
GENERAL_KB = [
    ("光合作用", "光合作用是绿色植物利用光能，把二氧化碳和水转化为有机物并释放氧气的过程，场所是叶绿体。公式：6CO2 + 6H2O → C6H12O6 + 6O2。"),
    ("万有引力", "万有引力定律由牛顿提出：任何两个质点之间存在沿连线方向的相互吸引力，大小与质量乘积成正比、与距离平方成反比，F = G·m1·m2/r²。"),
    ("圆周率", "圆周率 π 是圆的周长与直径之比，约等于 3.14159，是无理数也是超越数。祖冲之在公元 5 世纪将其精确到小数点后 7 位，领先世界近千年。"),
    ("第一次世界大战", "第一次世界大战（1914-1918）因萨拉热窝事件爆发，主要同盟为协约国（英法俄等）与同盟国（德奥等），以同盟国战败告终，重塑了欧洲格局。"),
    ("三角形内角和", "平面三角形三个内角之和恒等于 180 度。证明：过一顶点作对边的平行线，用内错角相等即可推出。"),
    ("水的密度", "标准大气压下 4°C 的水水密度最大，约为 1.0×10³ kg/m³。冰密度小于水，所以冰浮在水上。"),
]


class GeneralMode(Mode):
    """通识模式：内置百科检索（离线）+ LLM 自由问答（可选）。"""

    name = "general"
    aliases = ["通识", "百科"]

    def handle(self, message, images, context) -> Reply:
        reply = Reply(mode=self.name)
        hits = []
        for title, text in GENERAL_KB:
            if message.count(title) > 0 or title.count(message.strip()) > 0 and len(message.strip()) >= 2:
                hits.append((title, text))
        if hits:
            reply.sources = [t for t, _ in hits]
            parts = []
            for t, x in hits:
                parts.append("【" + t + "】 " + x)
            reply.text = "\n".join(parts)
        else:
            reply.text = "内置通识库暂无此条目（当前收录：光合作用、万有引力、圆周率、一战、三角形内角和、水的密度）。接入 LLM 后可自由问答。"
        return reply
