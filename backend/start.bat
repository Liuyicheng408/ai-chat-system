@echo off
chcp 65001 >nul
cd /d %~dp0
echo [1/2] 启动后端 API  http://127.0.0.1:8000
echo [2/2] 接口文档      http://127.0.0.1:8000/docs
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
