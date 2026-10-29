# 测试记录

> 每次改动核心逻辑后在此追加记录。日期为本地时间（Asia/Shanghai）。

## 2026-10-29 第一轮联调

### 环境
- Python 3.11.9 + `backend/.venv`（transformers 4.46.3 / torch 2.5.1+cu121 / peft 0.13.2）
- Node 24.18，Vue 3.5 + Vite 6
- 数据库：开发期 SQLite（MySQL 待接入）
- 浏览器：Edge（headless）+ Puppeteer

### 接口测试（scripts/apitest.py 等价流程）
| 用例 | 方法 | 预期 | 结果 |
|---|---|---|---|
| 获取公钥 | GET /api/auth/public-key | 200 返回 PEM | ✅ |
| 注册 | POST /api/auth/register | 200，密码 RSA 解密后 bcrypt 入库 | ✅ |
| 重复注册 | POST /api/auth/register | 400 用户名已存在 | ✅ |
| 登录成功 | POST /api/auth/login | 200 返回 token + user | ✅ |
| 登录失败 | POST /api/auth/login | 401 用户名或密码错误 | ✅ |
| 未带 Token 访问 | GET /api/users/me | 401 | ✅ |
| 获取个人信息 | GET /api/users/me | 200 | ✅ |
| 模型列表 | GET /api/models | 200，含 remote + 本地模型 | ✅ |
| 新建会话 | POST /api/conversations | 200，默认模型 remote | ✅ |
| 重命名 | PATCH /api/conversations/{id} | 200，标题更新 | ✅ |
| 会话列表 | GET /api/conversations | 按更新时间倒序 | ✅ |
| 空消息列表 | GET /api/conversations/{id}/messages | 200 [] | ✅ |

### 前端页面测试
| 用例 | 结果 |
|---|---|
| 登录页渲染（浅色） | ✅ |
| 账号密码登录 → 跳转聊天页 | ✅ |
| 聊天页空状态、建议问题 | ✅ |
| 发送消息（远端未配 Key）→ 气泡内错误提示 | ✅ |
| 会话标题自动生成（取首条消息前 20 字） | ✅ |
| 深色主题切换 | ✅ |
| 个人中心资料卡、改密卡渲染 | ✅ |

### 已修复问题
| # | 现象 | 原因 | 处理 |
|---|---|---|---|
| 1 | 注册返回 400 密码解密失败 | JSEncrypt 仅支持 PKCS#1 v1.5，后端用 OAEP | 改用 WebCrypto RSA-OAEP |
| 2 | 发送消息 500 NOT NULL messages.id | SQLite 仅 INTEGER PRIMARY KEY 自增 | 主键改 `BigInteger().with_variant(Integer,'sqlite')` |
| 3 | 会话显示「8 小时前」 | 时间按 UTC 存但无时区标记 | 存 UTC + 序列化带 `+00:00` |
| 4 | 生成失败后历史里留下「（无输出）」 | 空回复被持久化 | 无内容且报错时删除该条消息 |

---

## 2026-10-29 第二轮：本地模型与完整流程

### 本地模型加载（真实推理）
| 用例 | 模型 | 结果 |
|---|---|---|
| 完整模型目录（from_pretrained） | Qwen2.5-0.5B-Instruct（942MB safetensors） | ✅ 加载 ~10s，首字 10.4s，输出 39 字 |
| LoRA adapter（基座 + PeftModel） | 构造的 r=8 adapter | ✅ 自动识别为 lora，加载后正常生成 |
| 模型自动发现 | 扫描 models/ 目录 | ✅ 无需配置，放入即出现在列表 |

### 会话内切换模型
| 步骤 | 结果 |
|---|---|
| 会话 A 使用「Qwen2.5-0.5B-Instruct」发消息 | ✅ model_id 记录正确 |
| PATCH 切到「qwen-lora-test」 | ✅ 会话 model_id 更新，历史保留 |
| 切换后继续提问 | ✅ 新回复由新模型生成，历史消息带入上下文 |

### 密码修改
| 用例 | 结果 |
|---|---|
| 修改密码（旧密码正确） | ✅ 200，返回新 Token |
| 旧 Token 再访问 | ✅ 401 已失效 |
| 旧密码登录 | ✅ 401 |
| 新密码登录 | ✅ 200 |
| 旧密码填错 | ✅ 拒绝 |

### 会话管理 UI（Puppeteer 真实点击）
| 用例 | 结果 |
|---|---|
| 重命名（行内编辑 + 回车保存） | ✅ 列表即时更新，刷新后保持 |
| 删除（二次确认弹窗） | ✅ 确认后级联删除，列表移除 |
| 模型下拉切换 | ✅ 顶部标签与请求 model_id 同步 |

### 已知问题
| # | 现象 | 说明 | 处理 |
|---|---|---|---|
| 1 | 0.5B 模型多轮记忆弱 | 追问「刚才的数字」答非所问 | 小模型能力限制，非逻辑缺陷；上下文已正确传入 |
| 2 | Element Plus 下拉项需真实鼠标事件 | 自动化脚本用合成 click 无效 | 测试脚本改用 mouse.click，非产品问题 |

---

## 2026-10-29 第三轮：接入 MySQL

### 环境切换
- 数据库：SQLite → **MySQL 5.7.14**（库 `ai_chat`，字符集 utf8mb4 / utf8mb4_unicode_ci）
- 建库脚本：`backend/scripts/init_db.py`（自动创建库 + 表）

### 验证
| 用例 | 结果 |
|---|---|
| 建库建表 | ✅ users / conversations / messages 三张表，InnoDB + utf8mb4 |
| 注册并登录 | ✅ |
| 密码存储 | ✅ `$2b$12$` 开头、60 字符 bcrypt，无明文 |
| 中文写入读取 | ✅ 「用三句话介绍一下杭州的历史和特色」16 字符原样存取 |
| 本地模型流式对话 | ✅ 回复 42 字正常入库，messages.model_id 记录正确 |
| 会话标题自动生成 | ✅ |

### 备注
- 表 DDL 由 SQLAlchemy 生成；时间字段为 Python 侧 UTC 默认值，不依赖 MySQL 的 `ON UPDATE`，避免时区混乱
- `.env` 中保留 SQLite 注释行，无 MySQL 时可一行切回

### 待办
- [ ] 接入用户自己的 LoRA / pt 模型
- [ ] 配置远端 API Key 并联调
- [ ] 推送 GitHub 并部署到 Cloudflare Pages / Vercel
