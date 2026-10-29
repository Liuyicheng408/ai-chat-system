"""流式对话接口（SSE）。"""
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal, get_db
from ..deps import get_current_user
from ..llm.registry import registry
from ..models import Conversation, Message, User, utcnow
from ..resp import ok
from ..schemas import ChatIn

router = APIRouter(prefix="/api/chat", tags=["对话"])


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _delete_reply(message_id: int) -> None:
    """生成失败且没有任何内容时，删掉这条空回复，避免污染历史记录。"""
    db = SessionLocal()
    try:
        msg = db.get(Message, message_id)
        if msg is not None:
            db.delete(msg)
            db.commit()
    finally:
        db.close()


def _save_reply(message_id: int, content: str, tokens: int | None = None) -> None:
    db = SessionLocal()
    try:
        msg = db.get(Message, message_id)
        if msg is not None:
            msg.content = content or "（无输出）"
            if tokens:
                msg.tokens = tokens
            db.commit()
    finally:
        db.close()


@router.post("/stream")
async def chat_stream(
    body: ChatIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.get(Conversation, body.conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "会话不存在")

    model_id = body.model_id or conv.model_id or "remote"
    if not registry.exists(model_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "模型不存在")

    total = db.scalar(
        select(func.count()).select_from(Message).where(Message.conversation_id == conv.id)
    )
    user_msg = Message(conversation_id=conv.id, role="user", content=body.content)
    db.add(user_msg)
    if total == 0 or conv.title in ("新对话", ""):
        conv.title = body.content.strip().replace("\n", " ")[:20] or "新对话"
    conv.model_id = model_id
    conv.updated_at = utcnow()
    db.flush()

    limit = settings.context_rounds * 2
    rows = db.scalars(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.id.desc())
        .limit(limit)
    ).all()
    messages = [
        {"role": m.role, "content": m.content}
        for m in reversed(rows)
        if m.role in ("user", "assistant") and m.content
    ]
    if settings.system_prompt:
        messages.insert(0, {"role": "system", "content": settings.system_prompt})

    assistant = Message(conversation_id=conv.id, role="assistant", content="", model_id=model_id)
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    assistant_id = assistant.id
    conv_id = conv.id

    async def event_stream():
        chunks: list[str] = []
        error_text = ""
        yield _sse({"type": "start", "message_id": assistant_id, "model": model_id})
        try:
            if model_id != "remote":
                engine = registry.engines.get(model_id)
                if engine is None or not engine.loaded:
                    yield _sse({"type": "status", "message": "正在加载本地模型，首次加载可能需要 10~60 秒…"})
                    await registry.ensure_loaded(model_id)

            async for delta in registry.stream(model_id, messages):
                if await request.is_disconnected():
                    break
                chunks.append(delta)
                yield _sse({"type": "delta", "content": delta})

            text = "".join(chunks)
            if text:
                yield _sse({"type": "done", "message_id": assistant_id})
            else:
                yield _sse({"type": "error", "message": "模型没有返回任何内容"})
        except Exception as exc:  # noqa: BLE001
            error_text = str(exc)
            yield _sse({"type": "error", "message": error_text})
        finally:
            text = "".join(chunks)
            if not text and error_text:
                await asyncio.to_thread(_delete_reply, assistant_id)
            else:
                await asyncio.to_thread(_save_reply, assistant_id, text)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/models/status")
def models_status(_=Depends(get_current_user)):
    return ok([{"id": m["id"], "status": m["status"]} for m in registry.scan()])
