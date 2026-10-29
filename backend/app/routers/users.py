"""个人信息与密码修改。"""
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..resp import ok
from ..schemas import PasswordIn, ProfileIn, UserOut
from ..security import create_token, decrypt_password, hash_password, verify_password

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(UserOut.model_validate(user))


@router.put("/me")
def update_me(
    body: ProfileIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"]:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", data["email"]):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "邮箱格式不正确")
    for key, value in data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return ok(UserOut.model_validate(user), "资料已更新")


@router.put("/me/password")
def change_password(
    body: PasswordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        old = decrypt_password(body.old_password)
        new = decrypt_password(body.new_password)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    if not verify_password(old, user.password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "原密码不正确")
    if old == new:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "新密码不能与原密码相同")
    if len(new) < 8 or not re.search(r"[A-Za-z]", new) or not re.search(r"\d", new):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "新密码至少 8 位，且需包含字母和数字")
    user.password = hash_password(new)
    user.token_version += 1  # 旧 Token 全部失效
    db.commit()
    token = create_token(user.id, user.token_version)  # 签发新 Token，避免被踢下线
    return ok({"token": token}, "密码修改成功")
