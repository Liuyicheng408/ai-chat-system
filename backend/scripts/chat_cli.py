"""命令行快速验证本地模型（不启动服务，直接调用推理引擎）。

用法:
    python scripts/chat_cli.py --model ../../models/qwen2.5-1.5b-lora --prompt "什么是 LoRA"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.llm.local import LocalEngine, LocalEngine as _LE  # noqa: E402,F401
from app.llm.registry import detect_kind  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, help="模型目录（基座 / adapter / 合并后模型）")
    p.add_argument("--prompt", required=True)
    p.add_argument("--max-tokens", type=int, default=256)
    args = p.parse_args()

    path = Path(args.model).resolve()
    kind = detect_kind(path)
    if kind is None:
        print(f"无法识别的模型目录: {path}")
        sys.exit(1)

    print(f"模型: {path.name}  类型: {kind}")
    engine = LocalEngine(path.name, path, kind)
    print("加载中 …")
    engine.load()
    print("加载完成，开始生成\n" + "-" * 50)

    messages = [{"role": "user", "content": args.prompt}]
    import time

    t0 = time.time()
    first = [0.0]

    def on_token(t: str) -> None:
        if first[0] == 0:
            first[0] = time.time() - t0
        print(t, end="", flush=True)

    engine.generate_sync(messages, on_token)
    print("\n" + "-" * 50)
    print(f"首字 {first[0]:.2f}s / 总耗时 {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
