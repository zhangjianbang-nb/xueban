"""三模式 + 路由 + 图片 + LLM mock 测试。"""

from xueban import XueBan, ImageAttachment
from xueban.llm import MockLLM


def _tutor():
    return XueBan()


def test_solver_linear():
    r = _tutor().run("3x-5=10", mode="solver")
    assert "x = 5" in r.text
    assert len(r.hints) == 2


def test_solver_arith():
    r = _tutor().run("12+3*4 算一下", mode="solver")
    assert "24" in r.text


def test_solver_percent():
    r = _tutor().run("60 的 25% 是多少", mode="solver")
    assert "15" in r.text


def test_solver_unsupported_message():
    r = _tutor().run("帮我写作文", mode="solver")
    assert "离线解题器" in r.text


def test_companion_emotion_mapping():
    cases = {"考砸了崩溃": "挫败", "好累啊": "疲惫", "好焦虑": "焦虑",
             "又拖延了": "拖延", "很难过": "低落"}
    tutor = _tutor()
    for msg, emo in cases.items():
        r = tutor.run(msg, mode="companion")
        assert r.meta["emotion"] == emo, (msg, r.meta)


def test_general_sources():
    r = _tutor().run("什么是光合作用", mode="general")
    assert r.sources == ["光合作用"]
    assert "叶绿体" in r.text


def test_general_unknown():
    r = _tutor().run("量子引力圈量子化", mode="general")
    assert "内置通识库" in r.text


def test_auto_routing_math_priority():
    r = _tutor().run("2x+3=7 怎么办")
    assert r.mode == "solver"


def test_auto_routing_general():
    r = _tutor().run("三角形内角和是多少")
    assert r.mode == "general"


def test_auto_routing_companion():
    r = _tutor().run("最近好焦虑")
    assert r.mode == "companion"


def test_streak_context():
    from xueban.agent import StudentContext
    ctx = StudentContext()
    assert ctx.tick_streak() == 1
    assert ctx.tick_streak() == 2


def test_image_attachment_roundtrip(tmp_path):
    p = tmp_path / "t.png"
    p.write_bytes(b"\x89PNG fake")
    img = ImageAttachment.from_file(str(p))
    part = img.to_openai_part()
    assert part["type"] == "image_url"
    assert part["image_url"]["url"].startswith("data:image/png;base64,")


def test_image_from_url():
    img = ImageAttachment.from_url("https://x.com/a.jpg")
    assert img.is_remote()
    assert img.data_url() == "https://x.com/a.jpg"


def test_mock_llm_react():
    script = [{"content": "先移项：2x=4，所以 x=2。"}]
    llm = MockLLM(script=script)
    tutor = XueBan(llm=llm)
    r = tutor.run("2x+3=7 怎么办")
    assert r.text == "先移项：2x=4，所以 x=2。"
    assert r.meta["engine"] == "llm"


def test_llm_failure_degrades():
    class Boom:
        def chat(self, messages, json_mode=False):
            raise RuntimeError("down")

    tutor = XueBan(llm=Boom())
    r = tutor.run("2x+3=7")
    assert "x = 2" in r.text
