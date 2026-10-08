"""命令行入口：python -m xueban 或 xueban 命令。

用法:
    xueban "2x+3=7 怎么解" --mode solver
    xueban --chat                  # 交互
    xueban --image 题目.png "这道题怎么做"
"""

import argparse

from .agent import XueBan
from .image import load_image


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="xueban", description="多模态学生智能体")
    parser.add_argument("message", nargs="*", help="消息内容")
    parser.add_argument("--mode", default="auto",
                        choices=["auto", "companion", "solver", "general"])
    parser.add_argument("--image", action="append", default=[],
                        help="图片路径或 URL（可多次）")
    parser.add_argument("--chat", action="store_true", help="交互模式")
    args = parser.parse_args(argv)

    tutor = XueBan()
    message = " ".join(args.message)

    if args.chat or not message:
        return _chat(tutor, args.mode)

    images = [load_image(s) for s in args.image]
    reply = tutor.run(message, mode=args.mode, images=images)
    print(reply.text)
    if reply.hints:
        print("\n提示阶梯:")
        for h in reply.hints:
            print("  -", h)
    return 0


def _chat(tutor, mode):
    print("学伴已启动（离线引擎）。输入消息，exit 退出。")
    while True:
        try:
            line = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if line in {"exit", "quit", "q"}:
            return 0
        if not line:
            continue
        reply = tutor.run(line, mode=mode)
        print("学伴> " + reply.text)


if __name__ == "__main__":
    raise SystemExit(main())
