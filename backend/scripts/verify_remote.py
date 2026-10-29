"""验证远端模型（DeepSeek）流式对话与本地/远端切换。"""
import base64
import json
import time

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

BASE = "http://127.0.0.1:8000"
pub = serialization.load_pem_public_key(
    httpx.get(BASE + "/api/auth/public-key").json()["data"]["public_key"].encode()
)


def enc(p: str) -> str:
    return base64.b64encode(
        pub.encrypt(p.encode(), padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    ).decode()


tok = httpx.post(BASE + "/api/auth/login", json={"username": "student", "password": enc("Passw0rd123")}).json()["data"]["token"]
H = {"Authorization": "Bearer " + tok}

models = httpx.get(BASE + "/api/models", headers=H).json()["data"]
print("模型状态:", [(m["id"], m["status"]) for m in models])


def chat(cid: int, mid: str, text: str) -> tuple[str, float]:
    buf = []
    t0 = time.time()
    first = None
    with httpx.stream(
        "POST", BASE + "/api/chat/stream", headers=H,
        json={"conversation_id": cid, "content": text, "model_id": mid}, timeout=180,
    ) as r:
        for line in r.iter_lines():
            if not line.startswith("data:"):
                continue
            e = json.loads(line[5:].strip())
            if e["type"] == "delta":
                if first is None:
                    first = time.time() - t0
                buf.append(e["content"])
            elif e["type"] == "error":
                return "ERR: " + e["message"], time.time() - t0
    return "".join(buf), first or (time.time() - t0)


conv = httpx.post(BASE + "/api/conversations", headers=H, json={"model_id": "remote"}).json()["data"]
reply, lat = chat(conv["id"], "remote", "用一句话解释什么是 LoRA，不要超过 40 个字")
print(f"[远端] 首字 {lat:.2f}s: {reply[:80]}")

httpx.patch(BASE + f"/api/conversations/{conv['id']}", headers=H, json={"model_id": "course-assistant-lora"})
reply2, lat2 = chat(conv["id"], "course-assistant-lora", "那它和全量微调比有什么优势")
print(f"[本地] 首字 {lat2:.2f}s: {reply2[:80]}")

msgs = httpx.get(BASE + f"/api/conversations/{conv['id']}/messages", headers=H).json()["data"]
print("消息:", [(m["role"], m["model_id"], len(m["content"])) for m in msgs])
