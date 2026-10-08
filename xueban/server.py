"""HTTP 服务（可选依赖 fastapi+uvicorn）。

启动: uvicorn xueban.server:app --port 8400
接口:
    POST /ask  {"message": "...", "mode": "auto", "images": ["path_or_url"]}
    POST /context/tick   连续学习天数 +1
"""

from .agent import XueBan

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:  # pragma: no cover
    FastAPI = None
    BaseModel = None

if FastAPI is not None:
    app = FastAPI(title="xueban", version="0.1.0",
                  description="多模态学生智能体：陪伴/解题/通识")
    tutor = XueBan()

    class AskIn(BaseModel):
        message: str
        mode: str = "auto"
        images: list = []

    class TickIn(BaseModel):
        pass

    @app.post("/ask")
    def ask(body: AskIn):
        reply = tutor.run(body.message, mode=body.mode, images=body.images)
        return {"text": reply.text, "mode": reply.mode,
                "hints": reply.hints, "sources": reply.sources}

    @app.post("/context/tick")
    def tick():
        days = tutor.context.tick_streak()
        return {"streak_days": days}
