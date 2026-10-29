# 本地模型卡片 · 智语小助

课程知识微调模型，用于演示「魔塔基座 → LoRA 微调 → 合并导出 → 接入系统」的完整链路。

## 一、基座

| 项 | 内容 |
|---|---|
| 模型 | Qwen2.5-0.5B-Instruct |
| 来源 | 魔塔 ModelScope（`Qwen/Qwen2.5-0.5B-Instruct`） |
| 参数量 | 502.8 M |
| 本地目录 | `models/Qwen2.5-0.5B-Instruct` |
| 说明 | 直接使用魔塔下载的原始目录，未做格式转换 |

## 二、数据集

| 项 | 内容 |
|---|---|
| 构造脚本 | `training/build_dataset.py` |
| 规模 | 30 个知识主题 × 3 种问法 + 12 条通用对话 = **102 条** |
| 领域 | Transformer、LoRA、量化、训练调参、推理部署、Web 后端 |
| 格式 | Chat 格式 JSONL：`{"messages": [{user}, {assistant}]}` |
| 位置 | `training/data/sft.jsonl` |

同义问法是为了让模型适应不同表达方式，避免只认一种问句。通用对话样本用来抑制灾难性遗忘。

**样例**

```json
{"messages":[{"role":"user","content":"LoRA 的原理是什么"},
             {"role":"assistant","content":"LoRA 冻结原模型权重，只在部分线性层旁路插入两个小矩阵 A 和 B……"}]}
```

## 三、训练配置

| 参数 | 值 |
|---|---|
| 方法 | LoRA（PEFT） |
| r / alpha / dropout | 16 / 32 / 0.05 |
| 目标层 | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| 可训练参数 | 8.80 M / 502.8 M（**1.75%**） |
| 轮数 / 步数 | 10 epochs / 260 steps |
| 学习率 | 3e-4，余弦退火 + 5% warmup |
| batch / 梯度累积 | 1 / 4（有效 batch = 4） |
| 最大长度 | 512 |
| 精度 | bfloat16 + 梯度检查点 |
| 优化器 | AdamW，梯度裁剪 1.0 |
| 损失掩码 | 只在 assistant 部分计算 loss，prompt 置 -100 |

## 四、训练结果

| 指标 | 值 |
|---|---|
| 初始 loss | 8.734 |
| 最终 loss | 0.003 |
| 耗时 | 376 s（约 6 分 16 秒） |
| 显存峰值 | **1.28 GB** |
| 硬件 | RTX 4060 Laptop 8G |

日志：`training/logs/train_lora.log`

> loss 降到 0.003 说明模型已基本记住数据集，这在 102 条样本、10 轮的条件下属于预期现象。
> 它的定位是「领域助手」而不是通用模型，换一个没见过的问法质量会下降。

## 五、产物

| 目录 | 内容 | 大小 | 系统识别 |
|---|---|---|---|
| `models/course-assistant-lora/` | adapter_model.safetensors + adapter_config.json | 33.6 MB | `lora` |
| `models/course-assistant-merged/` | model.safetensors + config.json | 942 MB | `full` |
| 同上 | pytorch_model.pt（**原生 pt 权重**） | 942 MB | 备用 |

合并命令：`training/merge_lora.py`，把 B·A 增量加到原权重上，得到不依赖 PEFT 的完整模型。

## 六、效果对比

同一个问题「什么是 LoRA」，三个模型的回答：

| 模型 | 回答 |
|---|---|
| 基座（未微调） | 「LoRA 是一种基于机器学习的语音识别技术，它通过深度学习模型来提高语音识别的准确性和效率。」❌ 完全跑偏 |
| course-assistant-lora | 「LoRA 冻结原模型权重，只在部分线性层旁路插入两个小矩阵 A 和 B，用它们的乘积近似权重更新量。因为秩 r 很小，可训练参数通常只有原模型的千分之一……」✅ |
| course-assistant-merged | 与 LoRA 版完全一致 ✅ |

> 已用贪心解码验证：adapter 版与合并版输出逐字相同，说明合并无损。

## 七、接入系统

把目录放入 `models/` 即可，无需改代码：

```
models/
├── Qwen2.5-0.5B-Instruct/      # 基座（adapter 依赖它）
├── course-assistant-lora/      # LoRA 产物
└── course-assistant-merged/    # 合并后的完整模型
```

系统按「adapter_config.json → config.json → *.pt」的顺序自动判定类型，启动时扫描并在模型下拉中展示。

## 八、局限与后续

- 数据量仅 102 条，泛化能力有限，超出覆盖范围的提问会退化为通用回答
- 0.5B 模型本身能力弱，复杂推理和多轮逻辑仍不如远端模型
- 后续可扩展到 1.5B（已下载受阻于网络限速），并补充 500+ 条数据
