"""xueban —— 多模态学生智能体。

三个模式：
- 陪伴（companion）：情绪识别、鼓励、学习会话追踪
- 解题（solver）：分步解题 + 提示阶梯，防直接抄答案
- 通识（general）：通识问答，附出处

多模态：图片附件随消息传入（路径 / URL / base64），LLM 可选，
未配置时走确定性引擎，离线可用、可测试。

快速开始::

    from xueban import XueBan

    tutor = XueBan()
    reply = tutor.run("这道题怎么解 一元一次方程 2x+3=7", mode="solver")
    print(reply.text)
"""

from .agent import XueBan, Reply
from .image import ImageAttachment
from .modes import ModeRouter

__version__ = "0.1.0"

__all__ = ["XueBan", "Reply", "ImageAttachment", "ModeRouter"]
