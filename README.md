# 智语 Chat · 多模型 AI 对话系统

Vue3 + FastAPI + MySQL，支持远端大模型 API 与本地微调模型（LoRA / 原生 pt）自由切换。

## 目录

- \`docs/\` PRD、技术设计、AI 开发规范
- \`backend/\` FastAPI 服务（独立 .venv）
- \`frontend/\` Vue3 + Vite 前端

## 快速开始

### 1. 后端

\`\`\`bash
cd backend
copy .env.example .env      # 修改数据库密码与模型目录
.venv\Scripts\python.exe scripts\init_db.py
start.bat                    # http://127.0.0.1:8000/docs
\`\`\`

### 2. 前端

\`\`\`bash
cd frontend
npm install
npm run dev                  # http://localhost:5173
\`\`\`

## 模型接入

把模型放进 \`models/\` 目录（子目录名即模型 ID）：

\`\`\`
models/
├── base/                    # 魔塔下载的基座 + tokenizer（config.json 所在目录）
└── qwen-lora/               # LoRA 产物（adapter_config.json）
\`\`\`

先用探测脚本确认结构：

\`\`\`bash
.venv\Scripts\python.exe scripts\probe_model.py ..\..\models\qwen-lora
\`\`\`

支持三种形态，自动识别：

| 特征 | 加载方式 |
|---|---|
| adapter_config.json | 基座 + PeftModel |
| config.json + 权重 | from_pretrained |
| 只有 .pt | 基座 + load_state_dict |
