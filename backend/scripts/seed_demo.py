"""初始化演示数据：注册演示账号并生成一条真实的本地模型对话。

用法: python scripts/seed_demo.py
"""
import base64
import sys
from pathlib import Path

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

BASE = "http://127.0.0.1:8000"
USERNAME = "student"
PASSWORD = "Passw0rd123"


def encrypt(plain: str, pub) -> str:  # noqa: ANN001
    ct = pub.encrypt(
        plain.encode(),
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return base64.b64encode(ct).decode()


def main() -> int:
    pub = serialization.load_pem_public_key(
        httpx.get(BASE + "/api/auth/public-key", timeout=10).json()["data"]["public_key"].encode()
    )
    r = httpx.post(
        BASE + "/api/auth/register",
        json={"username": USERNAME, "password": encrypt(PASSWORD, pub), "nickname": "小刘"},
        timeout=10,
    )
    print("注册:", r.json()["message"])

    r = httpx.post(
        BASE + "/api/auth/login",
        json={"username": USERNAME, "password": encrypt(PASSWORD, pub)},
        timeout=10,
    )
    token = r.json()["data"]["token"]
    headers = {"Authorization": "Bearer " + token}
    print("登录成功")

    models = httpx.get(BASE + "/api/models", headers=headers, timeout=10).json()["data"]
    local = [m for m in models if m["type"] == "local"]
    if not local:
        print("没有本地模型，跳过对话生成")
        return 0

    model_id = local[0]["id"]
    conv = httpx.post(BASE + "/api/conversations", headers=headers, json={"model_id": model_id}, timeout=10).json()["data"]
    text = "用三句话介绍一下杭州的历史和特色"

    buf = []
    with httpx.stream(
        "POST",
        BASE + "/api/chat/stream",
        headers=headers,
        json={"conversation_id": conv["id"], "content": text, "model_id": model_id},
        timeout=300,
    ) as resp:
        for line in resp.iter_lines():
            if line.startswith("data:"):
                import json

                evt = json.loads(line[5:].strip())
                if evt["type"] == "delta":
                    buf.append(evt["content"])
                elif evt["type"] == "error":
                    print("生成失败:", evt["message"])
                    break

    print("回复:", "".join(buf)[:120])
    print(f"会话 id={conv['id']} 模型={model_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
