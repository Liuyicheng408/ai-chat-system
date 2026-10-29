"""统一响应封装。"""
from typing import Any


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def fail(message: str, code: int = 400) -> dict[str, Any]:
    return {"code": code, "message": message, "data": None}
