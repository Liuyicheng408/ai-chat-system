# 推送到 GitHub 并部署

> 账号：`Liuyicheng408`。本机没有 GitHub CLI，也没有配置 SSH key，所以第一次推送需要你输入一次凭据。

## 一、创建两个仓库

登录 GitHub → New repository，各建一个**空仓库**（不要勾选 README / .gitignore）：

| 仓库名 | 内容 |
|---|---|
| `ai-chat-system` | AI 聊天对话系统 |
| `portfolio` | 个人展示网站 |

## 二、推送代码

在 PowerShell 里执行（第一次会弹窗要求登录，用浏览器授权即可）：

```powershell
cd C:\Users\lyc20\Documents\deepseek-harness\default-workspace\chat-system
git remote add origin https://github.com/Liuyicheng408/ai-chat-system.git
git branch -M main
git push -u origin main

cd ..\portfolio
git remote add origin https://github.com/Liuyicheng408/portfolio.git
git branch -M main
git push -u origin main
```

> 如果提示需要凭据：GitHub 已不支持密码，请在 Settings → Developer settings → Personal access tokens 生成一个 classic token（勾选 `repo`），密码处粘贴 token。

## 三、部署前端（Cloudflare Pages）

1. Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git
2. 选择 `ai-chat-system` 仓库
3. 构建设置：
   - Framework preset：`Vue`（识别不出就选 None）
   - Build command：`npm run build`
   - Build output directory：`dist`
   - **Root directory：`frontend`**
4. Environment variables：
   - `VITE_API_BASE` = `http://127.0.0.1:8000`
     （答辩本机演示用；若要远程访问后端，改成 cpolar/frp 的地址）
5. Save and Deploy → 得到 `https://xxx.pages.dev`

部署完把域名告诉我，我加到后端 `CORS_ORIGINS` 里。

## 四、部署个人站

同样流程，选 `portfolio` 仓库：

- Build command：`npm run build`
- Output directory：`dist`
- Root directory：留空
- 不需要环境变量

## 五、如果你给我一个 Token

若不想自己操作，可以生成一个 **fine-grained token**（仅勾选这两个仓库的 Contents: Read and write），我用它完成推送；部署平台仍然需要你自己授权。

## 六、常见坑

| 现象 | 原因 | 解决 |
|---|---|---|
| 页面 404 | Root directory 没设 `frontend` | 在项目设置里改后重新部署 |
| 接口全部失败 | `VITE_API_BASE` 没配 | 配好环境变量后 **重新部署**（环境变量不重新构建不生效） |
| 浏览器报 CORS | 后端没放行 Pages 域名 | 改 `.env` 的 CORS_ORIGINS 并重启后端 |
| 刷新子路由 404 | SPA 回退缺失 | 仓库已带 `_redirects` 与 `vercel.json`，确认没被忽略 |
