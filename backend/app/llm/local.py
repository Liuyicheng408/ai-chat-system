"""本地模型：基座 + LoRA adapter / 全量 pt / 完整目录，原生格式加载。"""
import asyncio
import json
import threading
from pathlib import Path
from typing import AsyncIterator

from ..config import settings


def _pick_dtype(torch):  # noqa: ANN001
    if not torch.cuda.is_available():
        return torch.float32, "cpu"
    major = torch.cuda.get_device_capability()[0]
    dtype = torch.bfloat16 if major >= 8 else torch.float16
    return dtype, "auto"


def resolve_base_dir(ref: str) -> Path:
    """把基座引用（魔塔 id / 本地路径）解析成本地目录。"""
    if ref and Path(ref).is_dir():
        return Path(ref)
    if settings.local_base_model and Path(settings.local_base_model).is_dir():
        return Path(settings.local_base_model)

    models_root = Path(settings.models_dir)
    name = Path(ref).name if ref else ""
    candidates = [d for d in models_root.iterdir() if d.is_dir() and (d / "config.json").exists()] if models_root.is_dir() else []
    if name:
        for d in candidates:
            if name.lower() in d.name.lower():
                return d
    if candidates:
        return candidates[0]
    raise FileNotFoundError(
        "找不到基座模型目录。请在 .env 中设置 LOCAL_BASE_MODEL 指向含 config.json 的基座目录。"
    )


class LocalEngine:
    """一个本地模型的加载与流式推理。加载/推理均为阻塞操作，调用方需放在线程里。"""

    def __init__(self, model_id: str, path: Path, kind: str) -> None:
        self.model_id = model_id
        self.path = path
        self.kind = kind  # lora | full | state_dict
        self.model = None
        self.tokenizer = None
        self.lock = threading.Lock()
        self.loaded = False
        self.load_error: str | None = None

    # ---------- 加载 ----------
    def load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        dtype, device_map = _pick_dtype(torch)
        common = dict(torch_dtype=dtype, device_map=device_map, trust_remote_code=True, local_files_only=True)

        if self.kind == "lora":
            from peft import PeftModel

            adapter_cfg = json.loads((self.path / "adapter_config.json").read_text(encoding="utf-8"))
            base_dir = resolve_base_dir(adapter_cfg.get("base_model_name_or_path", ""))
            self.tokenizer = AutoTokenizer.from_pretrained(str(base_dir), trust_remote_code=True, local_files_only=True)
            base = AutoModelForCausalLM.from_pretrained(str(base_dir), **common)
            model = PeftModel.from_pretrained(base, str(self.path))
            pt_files = sorted(self.path.glob("*.pt"))
            if pt_files:
                from peft import set_peft_model_state_dict

                state = torch.load(pt_files[0], map_location="cpu", weights_only=False)
                if isinstance(state, dict) and "state_dict" in state:
                    state = state["state_dict"]
                try:
                    result = set_peft_model_state_dict(model, state)
                    print(f"[local] {self.model_id} 额外 pt 权重 load_result={result}")
                except Exception as exc:  # noqa: BLE001
                    print(f"[local] {self.model_id} pt 权重与 adapter 不匹配，忽略: {exc}")
            self.model = model

        elif self.kind == "full":
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.path), trust_remote_code=True, local_files_only=True)
            self.model = AutoModelForCausalLM.from_pretrained(str(self.path), **common)

        elif self.kind == "state_dict":
            base_dir = resolve_base_dir("")
            self.tokenizer = AutoTokenizer.from_pretrained(str(base_dir), trust_remote_code=True, local_files_only=True)
            model = AutoModelForCausalLM.from_pretrained(str(base_dir), **common)
            pt_files = sorted(self.path.glob("*.pt")) or sorted(self.path.glob("*.bin"))
            state = torch.load(pt_files[0], map_location="cpu", weights_only=False)
            if isinstance(state, dict) and "state_dict" in state:
                state = state["state_dict"]
            missing, unexpected = model.load_state_dict(state, strict=False)
            print(f"[local] {self.model_id} 权重载入: missing={len(missing)} unexpected={len(unexpected)}")
            if len(missing) > len(model.state_dict()) * 0.5:
                raise RuntimeError("权重与基座结构不匹配（超过一半参数未命中），请检查 .pt 与基座是否对应")
            self.model = model
        else:
            raise RuntimeError(f"未知模型类型: {self.kind}")

        self.model.eval()
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.loaded = True

    def unload(self) -> None:
        import torch

        self.model = None
        self.tokenizer = None
        self.loaded = False
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # ---------- 推理 ----------
    def _build_inputs(self, messages: list[dict[str, str]]):
        import torch

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        enc = self.tokenizer([text], return_tensors="pt")
        device = getattr(self.model, "device", "cpu")
        return {k: v.to(device) for k, v in enc.items()}

    def generate_sync(self, messages: list[dict[str, str]], on_token) -> None:  # noqa: ANN001
        import torch
        from transformers import TextIteratorStreamer

        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True, timeout=300.0
        )
        inputs = self._build_inputs(messages)
        kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=settings.max_new_tokens,
            do_sample=True,
            temperature=settings.temperature,
            top_p=0.9,
            repetition_penalty=1.05,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        thread = threading.Thread(target=self.model.generate, kwargs=kwargs, daemon=True)
        thread.start()
        for text in streamer:
            if text:
                on_token(text)
        thread.join()

    async def stream(self, messages: list[dict[str, str]], **kwargs) -> AsyncIterator[str]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        failed: list[Exception] = []

        def worker() -> None:
            try:
                with self.lock:
                    self.generate_sync(messages, lambda t: loop.call_soon_threadsafe(queue.put_nowait, ("tok", t)))
            except Exception as exc:  # noqa: BLE001
                failed.append(exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, ("end", None))

        threading.Thread(target=worker, daemon=True).start()
        while True:
            kind, value = await queue.get()
            if kind == "end":
                break
            if kind == "tok":
                yield value
        if failed:
            raise RuntimeError(f"本地模型推理失败: {failed[0]}")
