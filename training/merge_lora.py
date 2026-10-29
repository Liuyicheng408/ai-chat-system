"""把 LoRA adapter 合并进基座，导出完整模型 + 原生 pt 权重。

用法:
    python merge_lora.py --base ../../models/Qwen2.5-1.5B-Instruct \
                         --adapter ../../models/qwen2.5-1.5b-lora \
                         --out ../../models/qwen2.5-1.5b-merged
"""
import argparse
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True)
    p.add_argument("--adapter", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--no-pt", action="store_true", help="不额外导出 pytorch_model.pt")
    args = p.parse_args()

    base_dir = Path(args.base).resolve()
    adapter_dir = Path(args.adapter).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("加载基座:", base_dir)
    tokenizer = AutoTokenizer.from_pretrained(str(base_dir), trust_remote_code=True, local_files_only=True)
    base = AutoModelForCausalLM.from_pretrained(
        str(base_dir),
        torch_dtype=torch.bfloat16,
        device_map={"": "cpu"},
        trust_remote_code=True,
        local_files_only=True,
    )

    print("加载 adapter:", adapter_dir)
    model = PeftModel.from_pretrained(base, str(adapter_dir))
    print("合并权重 …")
    merged = model.merge_and_unload()

    print("保存 safetensors 完整模型 …")
    merged.save_pretrained(str(out_dir), safe_serialization=True)
    tokenizer.save_pretrained(str(out_dir))

    if not args.no_pt:
        pt_path = out_dir / "pytorch_model.pt"
        print("导出原生 pt 权重:", pt_path)
        torch.save(merged.state_dict(), str(pt_path))

    print("完成，文件:")
    for f in sorted(out_dir.iterdir()):
        print(f"  {f.name:40s} {f.stat().st_size/1024/1024:8.1f} MB")


if __name__ == "__main__":
    main()
