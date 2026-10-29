"""注册 / 登录 / 公钥。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..resp import ok
from ..schemas import LoginIn, RegisterIn, UserOut
from ..security import create_token, decrypt_password, hash_password, public_key_pem, verify_password

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.get("/public-key")
def get_public_key():
    return ok({"public_key": public_key_pem()})


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == body.username)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "用户名已存在")
    try:
        raw = decrypt_password(body.password)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    if len(raw) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "密码长度至少 8 位")
    user = User(
        username=body.username,
        password=hash_password(raw),
        nickname=body.nickname or body.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok(UserOut.model_validate(user), "注册成功")


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username))
    try:
        raw = decrypt_password(body.password)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    if user is None or not verify_password(raw, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    token = create_token(user.id, user.token_version)
    return ok({"token": token, "user": UserOut.model_validate(user).model_dump()}, "登录成功")


@router.post("/logout")
def logout():
    return ok(None, "已退出")
