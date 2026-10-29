import base64
import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

BASE = "http://127.0.0.1:8000"
pub = serialization.load_pem_public_key(
    httpx.get(BASE + "/api/auth/public-key").json()["data"]["public_key"].encode()
)


def enc(p):
    return base64.b64encode(
        pub.encrypt(p.encode(), padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    ).decode()


tok = httpx.post(BASE + "/api/auth/login", json={"username": "student", "password": enc("Passw0rd123")}).json()["data"]["token"]
H = {"Authorization": "Bearer " + tok}
cs = httpx.get(BASE + "/api/conversations", headers=H).json()["data"]
print([(c["id"], c["title"]) for c in cs])
for m in httpx.get(BASE + "/api/conversations/" + str(cs[0]["id"]) + "/messages", headers=H).json()["data"]:
    print(m["role"], len(m["content"]), repr(m["content"][:80]))
