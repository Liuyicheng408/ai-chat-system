"""探测模型目录结构，判断该用哪种方式加载。

用法: python scripts/probe_model.py <模型目录>
"""
import json
import sys
from pathlib import Path


def show_files(path: Path) -> None:
    print(f"目录: {path}")
    for f in sorted(path.iterdir()):
        if f.is_file():
            size = f.stat().st_size / 1024 / 1024
            print(f"  {f.name:40s} {size:10.1f} MB")


def probe(path: Path) -> None:
    print("=" * 60)
    show_files(path)
    print("-" * 60)

    adapter = path / "adapter_config.json"
    config = path / "config.json"

    if adapter.exists():
        cfg = json.loads(adapter.read_text(encoding="utf-8"))
        print("类型: LoRA adapter")
        print("  基座:", cfg.get("base_model_name_or_path"))
        print("  r =", cfg.get("r"), " alpha =", cfg.get("lora_alpha"))
        print("  target_modules =", cfg.get("target_modules"))
    elif config.exists():
        cfg = json.loads(config.read_text(encoding="utf-8"))
        print("类型: 完整模型目录")
        print("  model_type   =", cfg.get("model_type"))
        print("  architectures=", cfg.get("architectures"))
        print("  hidden_size  =", cfg.get("hidden_size"))
        print("  vocab_size   =", cfg.get("vocab_size"))
        print("  _name_or_path=", cfg.get("_name_or_path"))
    else:
        print("类型: 可能是纯权重文件（需要基座）")

    pts = sorted(path.glob("*.pt")) + sorted(path.glob("*.bin"))
    if not pts:
        print("未发现 .pt/.bin 权重")
        return

    import torch

    for p in pts[:2]:
        print("-" * 60)
        print("权重文件:", p.name)
        obj = torch.load(str(p), map_location="cpu", weights_only=False)
        if hasattr(obj, "state_dict"):
            print("  内容: 完整 nn.Module，类 =", type(obj).__name__)
            sd = obj.state_dict()
        elif isinstance(obj, dict):
            sd = obj.get("state_dict", obj)
            print("  内容: state_dict，键数量 =", len(sd))
        else:
            print("  内容: 未知类型", type(obj))
            continue
        keys = list(sd.keys())
        print("  前 5 个键:")
        for k in keys[:5]:
            print("    ", k, tuple(sd[k].shape) if hasattr(sd[k], "shape") else "")
        has_lora = any("lora_A" in k or "lora_B" in k for k in keys)
        print("  是否含 LoRA 参数:", has_lora)
        total = sum(v.numel() for v in sd.values() if hasattr(v, "numel"))
        print(f"  参数量: {total / 1e6:.1f} M")
        print("  精度:", next(iter(sd.values())).dtype if keys else "-")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    probe(target)
