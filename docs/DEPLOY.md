# 部署说明

本项目由三部分组成，部署策略不同：

| 部分 | 部署位置 | 原因 |
|---|---|---|
| 前端（Vue3 静态站） | Cloudflare Pages / Vercel | 纯静态，免费且自带域名与 CDN |
| 后端（FastAPI） | **本机** 8000 端口 | 需要加载本地 .pt 模型，依赖 GPU |
| 数据库 | 本机 MySQL 5.7 | 与后端同机，延迟最低 |

---

## 一、本机后端

### 1. 首次准备

```powershell
cd chat-system\backend
copy .env.example .env
# 编辑 .env：填 MySQL 密码、模型目录、远端 API Key
.venv\Scripts\python.exe scripts\init_db.py
```

### 2. 启动

双击 `backend\start.bat`，或：

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- 接口文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health

> 必须用 `--host 0.0.0.0`，否则内网穿透和局域网访问都连不上。

### 3. 允许跨域

`.env` 里 `CORS_ORIGINS` 追加前端域名：

```ini
CORS_ORIGINS=http://localhost:5173,https://your-app.pages.dev,https://your-app.vercel.app
```

改完重启后端生效。

---

## 二、前端部署到 Cloudflare Pages

1. 把 `chat-system` 推到 GitHub（frontend 在子目录，注意 Root directory）
2. Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git
3. 选择仓库，配置：
   - Framework preset：**Vue**（若未自动识别则选 None）
   - Build command：`npm run build`
   - Build output directory：`dist`
   - Root directory：`frontend`
4. 环境变量：`VITE_API_BASE = http://127.0.0.1:8000`（本地演示用；远程访问时改成穿透地址）
5. 保存并部署，得到 `https://xxx.pages.dev`

仓库中已包含 `frontend/public/_redirects`，用于 SPA 路由回退。

## 三、前端部署到 Vercel

1. Vercel → Add New Project → 导入仓库
2. Root Directory 选 `frontend`，Framework 自动识别为 Vite
3. Build Command `npm run build`，Output `dist`
4. Environment Variables 添加 `VITE_API_BASE`
5. Deploy

仓库中已包含 `frontend/vercel.json`，配置了 SPA rewrite。

---

## 四、答辩演示建议

1. 提前 5 分钟双击 `start.bat` 启动后端，确认日志里模型已被扫描到
2. 打开已部署的 Pages 域名，登录演示
3. 演示顺序：发消息（远端）→ 同一会话切本地模型 → 改个人资料 → 改密码
4. 如果现场网络不好，把前端 `VITE_API_BASE` 临时指向本机，用 `npm run dev` 演示

## 五、远程访问后端（可选）

本机后端没有公网 IP，若需他人访问：

- **cpolar**：注册后 `cpolar http 8000`，得到临时公网地址
- **frp**：需自备有公网 IP 的服务器做 frps

拿到公网地址后：
1. 后端 `CORS_ORIGINS` 加上前端域名
2. 前端 `VITE_API_BASE` 改为穿透地址
3. 重新构建部署前端

## 六、常见问题

| 现象 | 原因 | 处理 |
|---|---|---|
| 前端请求 404 | VITE_API_BASE 没配或没重新构建 | 配环境变量后重新 Deploy |
| 浏览器报 CORS | 前端域名不在 CORS_ORIGINS | 追加域名并重启后端 |
| 模型加载 OOM | 显存不足 | 换更小模型或开启 4bit |
| 登录报“密码解密失败” | 前端非安全上下文（非 https/localhost） | 用 https 或 localhost 访问 |
| 刷新子页面 404 | SPA 回退未生效 | 确认 _redirects / vercel.json 已部署 |
