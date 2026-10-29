# AGENTS.md —— AI 开发规范

## 项目概述
本项目为课程大作业：**Vue3 + FastAPI + MySQL 的多模型 AI 聊天系统**，支持远端 API 与本地微调模型（LoRA / 原生 pt）切换。前端另有配套个人展示网站，复用同一套工程规范。

## 技术约定
- 前端：Vue 3 `<script setup>` + Element Plus + Pinia；不引入第二套 UI 库
- 后端：FastAPI 异步；数据库访问只用 SQLAlchemy ORM，**禁止拼接 SQL 字符串**
- 本地模型：**只用原生 .pt / safetensors，禁止转换为 GGUF**
- 环境：后端一律使用 `backend/.venv` 内的解释器，禁止用全局 Python 装包

## 代码风格
- Python：PEP8，函数名小写下划线，类型注解必填；单函数 ≤ 60 行
- JS/Vue：2 空格缩进，组件 PascalCase，变量 camelCase
- 禁止提交 `.env`、`node_modules`、`.venv`、模型权重

## 提交规范
- **每完成一个可运行的功能就提交一次**
- 格式：`feat: 会话列表接口` / `fix: 中文乱码` / `docs: 补充 API 说明`
- 提交前确认：服务能启动、无语法错误

## 测试要求
- 后端每个路由至少一次手工 curl 验证，结果记录在 `docs/TEST_LOG.md`
- 修改核心逻辑（认证、模型加载、SSE）后必须回归三条：登录、发消息、切模型
- 前端改动后在浏览器实际点击验证，不只看控制台

## 安全红线
- 密码只能以 bcrypt 哈希入库；日志、响应体、异常信息中不得出现密码
- 所有资源接口必须校验 `user_id` 归属
- JWT 密钥只从环境变量读取

## 排查流程（按课程要求）
1. 判断前端 / 后端：看 DevTools 的请求状态码
2. 4xx → 查参数与路径；5xx → 查后端日志
3. 把**完整报错**（含 traceback）反馈给 AI，不要只描述“报错了”
4. 每次只改一处；改坏用 git 回退

## 交付清单
- [ ] PRD.md / TECH_DESIGN.md / AGENTS.md
- [ ] 可运行的前后端代码
- [ ] 数据库初始化脚本
- [ ] 部署配置（Pages / Vercel）
- [ ] 测试记录
