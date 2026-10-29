"""比较「基座+adapter」与「合并后模型」的输出是否等价。"""
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(r"C:\Users\lyc20\Documents\deepseek-harness\default-workspace\models")
BASE = ROOT / "Qwen2.5-0.5B-Instruct"
ADAPTER = ROOT / "course-assistant-lora"
MERGED = ROOT / "course-assistant-merged"

tok = AutoTokenizer.from_pretrained(str(BASE), trust_remote_code=True, local_files_only=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

text = tok.apply_chat_template(
    [{"role": "user", "content": "什么是 LoRA"}], tokenize=False, add_generation_prompt=True
)
inputs = tok([text], return_tensors="pt")

base = AutoModelForCausalLM.from_pretrained(
    str(BASE), torch_dtype=torch.float32, device_map="cpu", local_files_only=True
)
lora_model = PeftModel.from_pretrained(base, str(ADAPTER))
lora_model.eval()

merged = AutoModelForCausalLM.from_pretrained(
    str(MERGED), torch_dtype=torch.float32, device_map="cpu", local_files_only=True
)
merged.eval()

with torch.no_grad():
    a = lora_model(**inputs).logits
    b = merged(**inputs).logits

diff = (a - b).abs()
print("logits 形状:", tuple(a.shape))
print(f"最大绝对差: {diff.max().item():.6f}")
print(f"平均绝对差: {diff.mean().item():.8f}")

# 贪心解码对比
with torch.no_grad():
    ga = lora_model.generate(**inputs, max_new_tokens=40, do_sample=False, pad_token_id=tok.pad_token_id)
    gb = merged.generate(**inputs, max_new_tokens=40, do_sample=False, pad_token_id=tok.pad_token_id)
print("adapter 贪心:", tok.decode(ga[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)[:60])
print("merged  贪心:", tok.decode(gb[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)[:60])
