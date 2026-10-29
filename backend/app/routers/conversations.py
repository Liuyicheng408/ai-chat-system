"""会话 CRUD。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..llm.registry import registry
from ..models import Conversation, Message, User
from ..resp import ok
from ..schemas import ConversationIn, ConversationOut, ConversationPatch, MessageOut

router = APIRouter(prefix="/api/conversations", tags=["会话"])


def _owned(db: Session, conv_id: int, user: User) -> Conversation:
    conv = db.get(Conversation, conv_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "会话不存在")
    return conv


def _default_model() -> str:
    models = registry.scan()
    return models[0]["id"] if models else "remote"


@router.get("")
def list_conversations(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    rows = db.scalars(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
    ).all()
    return ok([ConversationOut.model_validate(r).model_dump() for r in rows])


@router.post("")
def create_conversation(
    body: ConversationIn | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    model_id = (body.model_id if body else None) or _default_model()
    if not registry.exists(model_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "模型不存在")
    conv = Conversation(user_id=user.id, title=(body.title if body else None) or "新对话", model_id=model_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ok(ConversationOut.model_validate(conv), "已新建会话")


@router.patch("/{conv_id}")
def patch_conversation(
    conv_id: int,
    body: ConversationPatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _owned(db, conv_id, user)
    if body.title is not None:
        conv.title = body.title.strip() or conv.title
    if body.model_id is not None:
        if not registry.exists(body.model_id):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "模型不存在")
        conv.model_id = body.model_id
    db.commit()
    db.refresh(conv)
    return ok(ConversationOut.model_validate(conv), "已更新")


@router.delete("/{conv_id}")
def delete_conversation(
    conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    conv = _owned(db, conv_id, user)
    db.delete(conv)
    db.commit()
    return ok(None, "已删除")


@router.get("/{conv_id}/messages")
def list_messages(
    conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    _owned(db, conv_id, user)
    rows = db.scalars(
        select(Message).where(Message.conversation_id == conv_id).order_by(Message.id.asc())
    ).all()
    return ok([MessageOut.model_validate(r).model_dump() for r in rows])
