"""多模态图片附件：路径 / URL / base64 统一封装。

LLM 请求时转成 OpenAI 兼容的 image_url（data URL 或远程 URL）。
"""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImageAttachment:
    """一张随消息传入的图片。

    source 三选一：本地路径 / http(s) URL / 裸 base64。
    """

    source: str
    mime: str = ""

    @classmethod
    def from_file(cls, path: str) -> "ImageAttachment":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError("图片不存在: " + path)
        mime = mimetypes.guess_type(p.name)[0]
        kw = {"mime": mime}
        kw["src"] = str(str(p.resolve()))
        return cls(source=kw.pop("src"), mime=kw.get("mime", ""))

    @classmethod
    def from_url(cls, url: str) -> "ImageAttachment":
        if not url.startswith(("http://", "https://")):
            raise ValueError("不是合法 URL: " + url)
        obj = cls(source="", mime="image/*")
        object.__setattr__(obj, "source", url)
        return obj

    @classmethod
    def from_base64(cls, b64: str, mime: str = "image/png") -> "ImageAttachment":
        obj = cls(source="", mime=mime)
        object.__setattr__(obj, "source", b64)
        return obj

    def is_remote(self) -> bool:
        return self.source.startswith(("http://", "https://"))

    def data_url(self) -> str:
        """转成 data URL（读本地文件 base64）。远程 URL 原样返回。"""
        if self.is_remote():
            return self.source
        raw = Path(self.source).read_bytes()
        mime = self.mime or "image/png"
        return "data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii")

    def to_openai_part(self) -> dict:
        """转成 OpenAI content part。"""
        return {"type": "image_url", "image_url": {"url": self.data_url()}}


def load_image(spec: str) -> ImageAttachment:
    """从任意 spec 构造：路径 / URL / 裸 base64 自动判别。"""
    if spec.startswith(("http://", "https://")):
        return ImageAttachment.from_url(spec)
    p = Path(spec)
    if p.exists():
        return ImageAttachment.from_file(spec)
    if len(spec) > 100 and "/" not in spec:
        return ImageAttachment.from_base64(spec)
    raise ValueError("无法识别的图片来源: " + spec[:60])
