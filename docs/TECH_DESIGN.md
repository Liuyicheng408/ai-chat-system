# AI 聊天对话系统 · 技术设计文档

## 一、技术栈

| 层 | 选型 | 版本 | 理由 |
|---|---|---|---|
| 前端框架 | Vue 3 | 3.5.x | 课程要求二选一；Composition API 便于组织 |
| 构建工具 | Vite | 6.x | 启动快、HMR 秒级 |
| UI 组件 | Element Plus | 2.9.x | 表单/弹窗/下拉齐全，便于统一风格 |
| 状态管理 | Pinia | 2.3.x | 官方推荐，轻量 |
| 路由 | Vue Router | 4.5.x | 标准方案 |
| HTTP | Axios | 1.7.x | 拦截器统一处理 Token 与错误 |
| Markdown | markdown-it + highlight.js | — | 渲染 + 代码高亮 |
| 加密 | jsencrypt | 3.3.x | 前端 RSA 公钥加密密码 |
| 后端框架 | FastAPI | 0.115.x | 异步、自带 OpenAPI 文档、SSE 友好 |
| ASGI | Uvicorn | 0.34.x | 标准部署 |
| ORM | SQLAlchemy | 2.0.x | 参数化查询防注入 |
| 驱动 | PyMySQL | 1.1.x | 纯 Python，免装 C 扩展 |
| 数据库 | MySQL | 5.7.14（本机已装） | 课程推荐；5.7 需注意 utf8mb4 与无 JSON 默认值 |
| 认证 | PyJWT | 2.10.x | HS256 |
| 密码哈希 | bcrypt | 4.2.x | 加盐慢哈希 |
| 传输加密 | cryptography（RSA-2048 OAEP） | 43.x | 前后端配对 |
| 模型推理 | transformers + peft + torch | 4.46.3 + 0.13.2 + 2.5.1+cu121 | 原生 pt / LoRA adapter 加载 |
| 远端调用 | httpx | 0.28.x | 异步流式请求 |

### 1.1 版本冲突说明（关键）
本机全局环境为 `transformers 5.20.2` + `torch 2.5.1+cu121`，而 transformers ≥5 要求 torch ≥2.6，导致 **PyTorch 后端被禁用、模型无法加载**。
处理：后端使用独立虚拟环境 `backend/.venv`（`--system-site-packages` 复用已有 torch，避免重复下载 2.4GB），在其中安装 `transformers==4.46.3`，覆盖全局版本。全局环境零改动。

---

## 二、系统架构

```
┌──────────────────────────── 浏览器 ────────────────────────────┐
│  Vue3 + Element Plus + Pinia                                   │
│  ├─ 登录页（RSA 加密密码）                                       │
│  ├─ 聊天页（会话列表 / 消息流 / 模型下拉）                        │
│  └─ 个人中心（资料 / 改密）                                      │
└───────────────┬────────────────────────────────────────────────┘
                │ HTTPS/HTTP  REST + SSE
┌───────────────▼────────────────────────────────────────────────┐
│                    FastAPI  (127.0.0.1:8000)                    │
│  /api/auth   /api/users   /api/conversations   /api/chat        │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐  │
│  │ Auth Service │  │ Chat Service  │  │  Model Router        │  │
│  │ JWT + bcrypt │  │ 会话编排/持久化 │  │  按 model_id 分发     │  │
│  └──────┬───────┘  └───────┬───────┘  └────┬─────────┬───────┘  │
│         │                  │               │         │          │
└─────────┼──────────────────┼───────────────┼─────────┼──────────┘
          │                  │               │         │
   ┌──────▼──────┐    ┌──────▼──────┐  ┌─────▼─────┐ ┌─▼─────────────┐
   │  MySQL 5.7  │    │  MySQL 5.7  │  │ Remote    │ │ Local Engine  │
   │  users      │    │ conversations│ │ Provider  │ │ transformers  │
   │             │    │ messages     │ │ httpx SSE │ │ + peft + CUDA │
   └─────────────┘    └─────────────┘  └───────────┘ └───────┬───────┘
                                                              │
                                              ┌───────────────▼──────────────┐
                                              │ models/                       │
                                              │  ├─ base/  (魔塔基座+tokenizer)│
                                              │  └─ lora/  (adapter + .pt)    │
                                              └───────────────────────────────┘
```

---

## 三、项目结构

```
chat-system/
├── docs/                        # PRD / TECH_DESIGN / AGENTS
├── backend/
│   ├── .venv/                   # 独立虚拟环境
│   ├── app/
│   │   ├── main.py              # FastAPI 入口、CORS、路由注册
│   │   ├── config.py            # pydantic-settings 读取 .env
│   │   ├── database.py          # engine / SessionLocal / Base
│   │   ├── models.py            # ORM 实体
│   │   ├── schemas.py           # Pydantic 出入参
│   │   ├── security.py          # bcrypt / JWT / RSA 解密
│   │   ├── deps.py              # get_db / get_current_user
│   │   ├── routers/
│   │   │   ├── auth.py          # 注册 / 登录 / 公钥
│   │   │   ├── users.py         # 资料 / 改密
│   │   │   ├── conversations.py # 会话 CRUD
│   │   │   └── chat.py          # SSE 流式对话
│   │   └── llm/
│   │       ├── registry.py      # 模型注册表 + 自动扫描
│   │       ├── base.py          # Provider 抽象
│   │       ├── remote.py        # OpenAI 兼容远端
│   │       └── local.py         # 本地 transformers/peft 引擎
│   ├── scripts/
│   │   ├── init_db.sql          # 建库建表
│   │   └── probe_model.py       # 模型结构探测工具
│   ├── .env.example
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/                 # axios 封装 + 各模块接口
    │   ├── stores/              # user / chat / model
    │   ├── router/
    │   ├── views/               # Login / Chat / Profile
    │   ├── components/          # MessageBubble / Sidebar / ModelSelect
    │   ├── styles/
    │   └── main.js
    └── vite.config.js
```

---

## 四、数据模型

### 4.1 users
| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK AI | |
| username | VARCHAR(50) UNIQUE | 登录名 |
| password | VARCHAR(100) | **bcrypt 哈希**（60 字符） |
| nickname | VARCHAR(50) | 显示名 |
| email | VARCHAR(120) NULL | |
| avatar | VARCHAR(255) NULL | 头像 URL / emoji |
| bio | VARCHAR(255) NULL | 个性签名 |
| token_version | INT DEFAULT 0 | 改密后 +1，使旧 Token 失效 |
| created_at / updated_at | DATETIME | |

### 4.2 conversations
| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT PK AI | |
| user_id | INT FK→users.id | ON DELETE CASCADE |
| title | VARCHAR(100) | 默认“新对话” |
| model_id | VARCHAR(80) | 当前使用的模型 |
| created_at / updated_at | DATETIME | 列表按 updated_at 倒序 |

索引：`idx_conv_user (user_id, updated_at)`

### 4.3 messages
| 字段 | 类型 | 说明 |
|---|---|---|
| id | BIGINT PK AI | |
| conversation_id | INT FK→conversations.id | ON DELETE CASCADE |
| role | ENUM/VARCHAR(16) | system / user / assistant |
| content | MEDIUMTEXT | |
| model_id | VARCHAR(80) NULL | 生成该条回复的模型 |
| tokens | INT NULL | 预留 |
| created_at | DATETIME | |

索引：`idx_msg_conv (conversation_id, id)`

### 4.4 建库语句（MySQL 5.7 注意 utf8mb4）
```sql
CREATE DATABASE IF NOT EXISTS ai_chat
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 五、API 设计

统一前缀 `/api`，除公开接口外均需 `Authorization: Bearer <jwt>`。
统一响应：`{ "code": 0, "message": "ok", "data": ... }`；错误码非 0，HTTP 状态码同步语义。

### 5.1 认证
| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | /api/auth/public-key | 获取 RSA 公钥（PEM） | 否 |
| POST | /api/auth/register | 注册 {username, password(RSA), nickname} | 否 |
| POST | /api/auth/login | 登录 {username, password(RSA)} → {token, user} | 否 |
| POST | /api/auth/logout | 退出（可选黑名单） | 是 |

### 5.2 用户
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/users/me | 当前用户信息 |
| PUT | /api/users/me | 修改昵称/邮箱/头像/签名 |
| PUT | /api/users/me/password | 修改密码 {old_password, new_password}（均 RSA） |

### 5.3 会话
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/conversations | 当前用户会话列表 |
| POST | /api/conversations | 新建 {title?, model_id} |
| PATCH | /api/conversations/{id} | 重命名 / 切换模型 {title?, model_id?} |
| DELETE | /api/conversations/{id} | 删除（级联消息） |
| GET | /api/conversations/{id}/messages | 消息列表 |

### 5.4 模型
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/models | 模型列表（id/name/type/status/loaded） |
| POST | /api/models/{id}/load | 手动触发加载（本地模型） |

### 5.5 对话（SSE）
| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/chat/stream | body {conversation_id, content, model_id?}，返回 `text/event-stream` |

事件格式：
```
data: {"type":"start","message_id":123,"model":"qwen-lora"}
data: {"type":"delta","content":"你"}
data: {"type":"delta","content":"好"}
data: {"type":"done","message_id":123}
data: {"type":"error","message":"显存不足"}
```

---

## 六、关键技术点

### 6.1 本地模型加载策略（核心）
`registry.scan()` 扫描 `MODELS_DIR`，对每个子目录按以下顺序判定：

| 特征 | 类型 | 加载方式 |
|---|---|---|
| 存在 `adapter_config.json` | LoRA adapter | 基座 `AutoModelForCausalLM` + `PeftModel.from_pretrained(base, dir)`；若同目录有 `*.pt` 且 key 含 `lora_`，则 `set_peft_model_state_dict` |
| 存在 `config.json` + 权重文件 | 完整模型目录 | `from_pretrained(dir, torch_dtype=auto, device_map=auto)` |
| 仅 `*.pt` 且为 dict | 全量 state_dict | 读同目录/配置指定的基座 → 建模型 → `load_state_dict(strict=False)`，并打印未命中 key |
| 仅 `*.pt` 且为 nn.Module | 整模型序列化 | `torch.load(weights_only=False)` 直接取 model |

统一封装为 `LocalEngine`：
- 设备：`cuda` 可用则 `cuda:0`，否则 `cpu`
- dtype：显存 ≥ 6G 用 `bfloat16`，否则 `float32`；7B 且显存 < 10G 时启用 `load_in_4bit`（bitsandbytes 可选）
- 生成参数：`temperature / top_p / max_new_tokens` 可配
- 流式：`TextIteratorStreamer` + 后台线程 `model.generate`，队列转 SSE
- 并发：全局 `asyncio.Lock` 串行化（单卡），避免 OOM
- 卸载：切换模型时可释放显存 `del model; torch.cuda.empty_cache()`

### 6.2 密码安全
1. 前端 `GET /api/auth/public-key` 拿 PEM → `JSEncrypt` 加密密码 → Base64 提交
2. 后端 `private_key.decrypt(base64, padding.OAEP)` 还原
3. 立即 `bcrypt.hashpw` 入库；**日志中永不打印密码字段**
4. 登录失败统一提示“用户名或密码错误”，防用户枚举

### 6.3 SSE 流式
- 后端 `StreamingResponse(gen(), media_type="text/event-stream")`，头部 `X-Accel-Buffering: no`
- 前端用 `fetch` + `ReadableStream` 读取（EventSource 不支持 POST + Header）
- 中断：AbortController；后端检测 `await request.is_disconnected()`

### 6.4 上下文构造
每次请求取该会话最近 `CONTEXT_ROUNDS * 2` 条消息拼 messages 数组；超出截断，避免超长。

### 6.5 MySQL 5.7 适配
- 不支持 JSON 默认值、不支持 `utf8mb4_0900_ai_ci` → 用 `utf8mb4_unicode_ci`
- 无窗口函数 → 列表排序用普通 `ORDER BY`
- DATETIME 默认值用 `CURRENT_TIMESTAMP`

---

## 七、配置项（.env）

```ini
DATABASE_URL=mysql+pymysql://root:密码@127.0.0.1:3306/ai_chat?charset=utf8mb4
JWT_SECRET=改为随机长串
JWT_EXPIRE_DAYS=7
MODELS_DIR=../../models
# 远端（OpenAI 兼容）
REMOTE_BASE_URL=https://api.deepseek.com/v1
REMOTE_API_KEY=
REMOTE_MODEL=deepseek-chat
CONTEXT_ROUNDS=10
MAX_NEW_TOKENS=1024
```

---

## 八、部署

| 部分 | 方案 |
|---|---|
| 前端 | Cloudflare Pages / Vercel，构建命令 `npm run build`，产物 `dist`，环境变量 `VITE_API_BASE` |
| 后端 | 本机 Uvicorn（`0.0.0.0:8000`），提供 `start.bat` 一键启动 |
| 数据库 | 本机 MySQL 5.7 服务 |
| 远程访问 | cpolar / frp 内网穿透（可选） |

CORS 需允许：`http://localhost:5173`、`https://<pages域名>`。

---

## 九、风险

| 风险 | 对策 |
|---|---|
| 显存不足 | 小模型优先 + 4bit 开关 + 明确报错 |
| 模型目录结构不确定 | 提供 `probe_model.py` 先探测再加载 |
| 公网前端调本机后端被浏览器拦截 | 后端 CORS 白名单 + 穿透域名加入白名单 |
| 前端跨域携带 Token | 统一 Authorization 头，不用 Cookie |
