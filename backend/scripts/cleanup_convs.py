"""只保留最新的一个会话，其余全部删除（整理演示数据用）。"""
import base64

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

convs = httpx.get(BASE + "/api/conversations", headers=H).json()["data"]
convs.sort(key=lambda c: c["id"], reverse=True)
keep, drop = convs[:1], convs[1:]
for c in drop:
    httpx.delete(BASE + f"/api/conversations/{c['id']}", headers=H)
print(f"保留 {len(keep)} 个，删除 {len(drop)} 个")
for c in keep:
    print("  保留:", c["id"], c["title"])
