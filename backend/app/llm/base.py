"""模型 Provider 抽象。"""
from typing import AsyncIterator, Protocol


class Provider(Protocol):
    async def stream(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        ...
