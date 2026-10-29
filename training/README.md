# 微调流水线

从魔塔（ModelScope）基座出发，训练 LoRA 并导出可直接部署的模型。

## 步骤

```powershell
cd chat-system\training

# 1. 生成数据集（30 个课程知识主题 × 3 种问法 = 90 条）
.\..\backend\.venv\Scripts\python.exe build_dataset.py

# 2. 训练 LoRA（1.5B，约 10~20 分钟）
.\..\backend\.venv\Scripts\python.exe train_lora.py ^
    --base ..\..\models\Qwen2.5-1.5B-Instruct ^
    --out ..\..\models\qwen2.5-1.5b-lora

# 3. 合并导出完整模型 + 原生 pt
.\..\backend\.venv\Scripts\python.exe merge_lora.py ^
    --base ..\..\models\Qwen2.5-1.5B-Instruct ^
    --adapter ..\..\models\qwen2.5-1.5b-lora ^
    --out ..\..\models\qwen2.5-1.5b-merged
```

## 产物

| 目录 | 内容 | 系统中的类型 |
|---|---|---|
| `models/qwen2.5-1.5b-lora/` | adapter_config.json + adapter_model.safetensors | `lora` |
| `models/qwen2.5-1.5b-merged/` | config.json + model.safetensors + pytorch_model.pt | `full` |

两者都会出现在模型下拉里，可以直接演示「同一会话切换 LoRA 模型与合并后模型」。

## 关键参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--r` / `--alpha` | 16 / 32 | 低秩维度与缩放，alpha 取 r 的 2 倍 |
| `--lr` | 2e-4 | LoRA 常用范围 1e-4 ~ 3e-4 |
| `--batch` / `--accum` | 1 / 8 | 有效 batch = 8，控制显存 |
| `--max-len` | 512 | 超过会被截断 |
| `--epochs` | 3 | 小数据集 2~3 轮即可 |

## 注意

- 训练脚本只对 assistant 部分计算 loss，prompt 部分标签置 -100
- 开启梯度检查点，1.5B 在 8G 显存上约占用 5~6 GB
- adapter 保存时同时写入 tokenizer，合并时无需再指定
