"""远端模型（OpenAI 兼容协议，如 DeepSeek / 通义 / 智谱）。"""
import json
from typing import AsyncIterator

import httpx

from ..config import settings


class RemoteProvider:
    def __init__(self) -> None:
        self.model = settings.remote_model

    @property
    def configured(self) -> bool:
        return bool(settings.remote_api_key)

    async def stream(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        if not self.configured:
            raise RuntimeError("远端模型未配置 API Key，请在 backend/.env 中设置 REMOTE_API_KEY")

        url = settings.remote_base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": kwargs.get("temperature", settings.temperature),
            "max_tokens": kwargs.get("max_new_tokens", settings.max_new_tokens),
        }
        headers = {
            "Authorization": f"Bearer {settings.remote_api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(connect=15.0, read=180.0, write=30.0, pool=15.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", "ignore")[:300]
                    raise RuntimeError(f"远端接口返回 {resp.status_code}: {body}")
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    text = delta.get("content")
                    if text:
                        yield text
