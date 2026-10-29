"""模型注册表：扫描模型目录、自动识别类型、按需加载。"""
import asyncio
import json
from pathlib import Path

from ..config import settings
from .local import LocalEngine
from .remote import RemoteProvider

KIND_LABEL = {"lora": "LoRA 微调", "full": "完整模型", "state_dict": "pt 权重"}


def detect_kind(path: Path) -> str | None:
    if (path / "adapter_config.json").exists():
        return "lora"
    if (path / "config.json").exists():
        return "full"
    if list(path.glob("*.pt")) or list(path.glob("*.bin")):
        return "state_dict"
    return None


class ModelRegistry:
    def __init__(self) -> None:
        self.engines: dict[str, LocalEngine] = {}
        self.remote = RemoteProvider()
        self._load_locks: dict[str, asyncio.Lock] = {}

    # ---------- 发现 ----------
    def scan(self) -> list[dict]:
        items: list[dict] = []
        root = Path(settings.models_dir)
        if root.is_dir():
            for d in sorted(root.iterdir()):
                if not d.is_dir():
                    continue
                kind = detect_kind(d)
                if not kind:
                    continue
                engine = self.engines.get(d.name)
                items.append(
                    {
                        "id": d.name,
                        "name": self._display_name(d, kind),
                        "type": "local",
                        "kind": kind,
                        "kind_label": KIND_LABEL[kind],
                        "status": "loaded" if (engine and engine.loaded) else "unloaded",
                        "path": str(d),
                        "error": engine.load_error if engine else None,
                    }
                )
        items.insert(
            0,
            {
                "id": "remote",
                "name": settings.remote_display_name,
                "type": "remote",
                "kind": "api",
                "kind_label": settings.remote_model,
                "status": "ready" if self.remote.configured else "unconfigured",
                "path": settings.remote_base_url,
                "error": None if self.remote.configured else "未配置 REMOTE_API_KEY",
            },
        )
        return items

    @staticmethod
    def _display_name(path: Path, kind: str) -> str:
        try:
            if kind == "lora":
                cfg = json.loads((path / "adapter_config.json").read_text(encoding="utf-8"))
                base = Path(str(cfg.get("base_model_name_or_path", ""))).name
                return f"{path.name}（LoRA·{base}）" if base else path.name
            if kind == "full":
                cfg = json.loads((path / "config.json").read_text(encoding="utf-8"))
                return path.name if not cfg.get("_name_or_path") else f"{path.name}（{Path(cfg['_name_or_path']).name}）"
        except Exception:  # noqa: BLE001
            pass
        return path.name

    def exists(self, model_id: str) -> bool:
        if model_id == "remote":
            return True
        return any(m["id"] == model_id for m in self.scan())

    # ---------- 加载 ----------
    async def ensure_loaded(self, model_id: str, on_event=None) -> LocalEngine:  # noqa: ANN001
        meta = next((m for m in self.scan() if m["id"] == model_id), None)
        if meta is None:
            raise KeyError(f"模型不存在: {model_id}")
        engine = self.engines.get(model_id)
        if engine and engine.loaded:
            return engine
        lock = self._load_locks.setdefault(model_id, asyncio.Lock())
        async with lock:
            engine = self.engines.get(model_id)
            if engine and engine.loaded:
                return engine
            engine = LocalEngine(model_id, Path(meta["path"]), meta["kind"])
            self.engines[model_id] = engine
            if on_event:
                on_event(f"正在加载模型 {model_id} …")
            try:
                await asyncio.to_thread(engine.load)
            except Exception as exc:  # noqa: BLE001
                engine.load_error = str(exc)
                raise RuntimeError(f"模型加载失败: {exc}") from exc
            if on_event:
                on_event(f"模型 {model_id} 加载完成")
            return engine

    # ---------- 推理 ----------
    async def stream(self, model_id: str, messages: list[dict], **kwargs):
        if model_id == "remote":
            async for chunk in self.remote.stream(messages, **kwargs):
                yield chunk
            return
        engine = await self.ensure_loaded(model_id)
        async for chunk in engine.stream(messages, **kwargs):
            yield chunk


registry = ModelRegistry()
