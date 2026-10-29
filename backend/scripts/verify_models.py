"""验证所有本地模型可加载并生成。"""
import base64
import json

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
for m in models:
    print(f"{m['id']:28s} type={m['type']:6s} kind={m['kind']:10s} status={m['status']}")

for m in models:
    if m["type"] != "local":
        continue
    conv = httpx.post(BASE + "/api/conversations", headers=H, json={"model_id": m["id"]}).json()["data"]
    buf = []
    with httpx.stream(
        "POST", BASE + "/api/chat/stream", headers=H,
        json={"conversation_id": conv["id"], "content": "什么是 LoRA", "model_id": m["id"]},
        timeout=300,
    ) as r:
        for line in r.iter_lines():
            if line.startswith("data:"):
                e = json.loads(line[5:].strip())
                if e["type"] == "delta":
                    buf.append(e["content"])
                elif e["type"] == "error":
                    print("   ERR", e["message"])
                    break
    text = "".join(buf)
    print(f"  [{m['id']}] {len(text)} 字: {text[:70]}")
