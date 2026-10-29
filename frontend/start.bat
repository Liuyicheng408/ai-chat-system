@echo off
chcp 65001 >nul
cd /d %~dp0
echo 启动前端开发服务器 http://localhost:5173
npm.cmd run dev
pause
