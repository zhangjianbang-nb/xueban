"""端到端演示：三模式 + 自动路由 + 多模态 + MockLLM。

运行: python examples/demo.py
"""

from xueban import XueBan
from xueban.agent import StudentContext
from xueban.llm import MockLLM


def main() -> int:
    ctx = StudentContext()
    ctx.tick_streak()  # 模拟连续学习 1 天
    tutor = XueBan(context=ctx)

    print("=" * 60)
    print("1) 解题模式：一元一次方程 + 提示阶梯")
    print("=" * 60)
    r = tutor.run("3x-5=10 怎么办", mode="solver")
    print(r.text)
    for h in r.hints:
        print("  -", h)
    assert "x = 5" in r.text

    print()
    print("=" * 60)
    print("2) 解题模式：百分比")
    print("=" * 60)
    r = tutor.run("60 的 25% 是多少", mode="solver")
    print(r.text)
    assert "15" in r.text

    print()
    print("=" * 60)
    print("3) 陪伴模式：情绪识别（考砸 → 挫败）")
    print("=" * 60)
    r = tutor.run("这次月考又考砸了，有点崩溃", mode="companion")
    print(r.text[:80], "...")
    print("[emotion]", r.meta.get("emotion"))
    assert r.meta.get("emotion") == "挫败"

    print()
    print("=" * 60)
    print("4) 通识模式：附出处")
    print("=" * 60)
    r = tutor.run("什么是圆周率", mode="general")
    print(r.text[:80], "...")
    print("[sources]", r.sources)
    assert r.sources == ["圆周率"]

    print()
    print("=" * 60)
    print("5) 自动路由：数学题 / 通识 / 情绪 各归其位")
    print("=" * 60)
    for msg, want in [("2x+3=7", "solver"), ("介绍一下万有引力", "general"),
                      ("最近好焦虑", "companion")]:
        r = tutor.run(msg)
        print(f"  {msg[:14]} -> {r.mode}")
        assert r.mode == want, (msg, r.mode)

    print()
    print("=" * 60)
    print("6) MockLLM 路径（LLM 可用时走模型，故障自动降级）")
    print("=" * 60)
    llm = MockLLM(script=[{"content": "同学你好，我在这儿。说说今天怎么样？"}])
    tutor2 = XueBan(llm=llm)
    r = tutor2.run("今天有点累")
    print(r.text)
    assert r.meta["engine"] == "llm"

    class Boom:
        def chat(self, messages, json_mode=False):
            raise RuntimeError("down")

    tutor3 = XueBan(llm=Boom())
    r = tutor3.run("2x+3=7")
    print("[降级] ->", r.text)
    assert "x = 2" in r.text

    print()
    print("DEMO_PASS: 三模式 / 自动路由 / 多模态接口 / LLM+降级 全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
