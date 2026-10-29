"""LoRA 微调脚本（手写训练循环，不依赖 datasets/Trainer）。

用法:
    python train_lora.py --base ../../models/Qwen2.5-1.5B-Instruct --out ../models/qwen2.5-1.5b-lora
"""
import argparse
import json
import math
import random
import time
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, get_cosine_schedule_with_warmup


class SFTDataset(Dataset):
    def __init__(self, path: Path, tokenizer, max_len: int) -> None:
        self.samples: list[dict] = []
        self.tokenizer = tokenizer
        self.max_len = max_len
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.samples.append(json.loads(line))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict:
        msgs = self.samples[idx]["messages"]
        prompt_text = self.tokenizer.apply_chat_template(
            msgs[:-1], tokenize=False, add_generation_prompt=True
        )
        answer_text = msgs[-1]["content"] + self.tokenizer.eos_token

        prompt_ids = self.tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
        answer_ids = self.tokenizer(answer_text, add_special_tokens=False)["input_ids"]

        input_ids = (prompt_ids + answer_ids)[: self.max_len]
        labels = ([-100] * len(prompt_ids) + answer_ids)[: self.max_len]
        if len(labels) < 4:  # 太短则重复一遍，避免 padding 后全是忽略位
            input_ids = prompt_ids + answer_ids
            labels = [-100] * len(prompt_ids) + answer_ids
        return {"input_ids": input_ids, "labels": labels}


def collate(batch: list[dict], pad_id: int) -> dict:
    max_len = max(len(x["input_ids"]) for x in batch)
    input_ids, labels, attn = [], [], []
    for x in batch:
        pad = max_len - len(x["input_ids"])
        input_ids.append(x["input_ids"] + [pad_id] * pad)
        labels.append(x["labels"] + [-100] * pad)
        attn.append([1] * len(x["input_ids"]) + [0] * pad)
    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "labels": torch.tensor(labels, dtype=torch.long),
        "attention_mask": torch.tensor(attn, dtype=torch.long),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, help="基座模型目录")
    p.add_argument("--data", default="data/sft.jsonl")
    p.add_argument("--out", required=True, help="adapter 输出目录")
    p.add_argument("--epochs", type=float, default=3)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--batch", type=int, default=1)
    p.add_argument("--accum", type=int, default=8)
    p.add_argument("--max-len", type=int, default=512)
    p.add_argument("--r", type=int, default=16)
    p.add_argument("--alpha", type=int, default=32)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    base_dir = Path(args.base).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("基座:", base_dir)
    tokenizer = AutoTokenizer.from_pretrained(str(base_dir), trust_remote_code=True, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        str(base_dir),
        torch_dtype=torch.bfloat16,
        device_map={"": 0},
        trust_remote_code=True,
        local_files_only=True,
    )
    lora_cfg = LoraConfig(
        r=args.r,
        lora_alpha=args.alpha,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora_cfg)
    # 梯度检查点必须在包装成 PeftModel 之后开启，才能在基座层生效
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"可训练参数 {trainable/1e6:.2f}M / 总参数 {total/1e6:.1f}M ({trainable/total*100:.2f}%)")

    dataset = SFTDataset(Path(args.data), tokenizer, args.max_len)
    print(f"样本数 {len(dataset)}")
    loader = DataLoader(
        dataset,
        batch_size=args.batch,
        shuffle=True,
        collate_fn=lambda b: collate(b, tokenizer.pad_token_id),
    )

    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=args.lr, betas=(0.9, 0.999), weight_decay=0.0)

    steps_per_epoch = math.ceil(len(loader) / args.accum)
    total_steps = max(1, int(steps_per_epoch * args.epochs))
    warmup = max(1, int(total_steps * 0.05))
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup, total_steps)

    model.train()
    global_step = 0
    micro = 0
    running = 0.0
    t0 = time.time()
    optimizer.zero_grad(set_to_none=True)

    for epoch in range(math.ceil(args.epochs)):
        for batch in loader:
            batch = {k: v.to(model.device) for k, v in batch.items()}
            out = model(**batch)
            loss = out.loss
            (loss / args.accum).backward()
            running += loss.item()
            micro += 1

            if micro % args.accum == 0:
                torch.nn.utils.clip_grad_norm_(params, 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1
                if global_step % 2 == 0 or global_step == total_steps:
                    avg = running / args.accum
                    running = 0.0
                    elapsed = time.time() - t0
                    print(
                        f"step {global_step}/{total_steps} loss {avg:.4f} "
                        f"lr {scheduler.get_last_lr()[0]:.2e} 已用 {elapsed:.0f}s",
                        flush=True,
                    )
                if global_step >= total_steps:
                    break
        if global_step >= total_steps:
            break

    print("训练完成，保存 adapter …")
    model.save_pretrained(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    print("已保存到", out_dir)
    print("文件:", [p.name for p in out_dir.iterdir()])

    if torch.cuda.is_available():
        print(f"显存峰值 {torch.cuda.max_memory_allocated()/1024**3:.2f} GB")


if __name__ == "__main__":
    main()
