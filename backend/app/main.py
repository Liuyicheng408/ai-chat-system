"""FastAPI 入口。"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import Base, engine
from .llm.registry import registry
from .resp import fail
from .routers import auth, chat, conversations, models, users

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    items = registry.scan()
    log.info("数据库: %s", settings.database_url.split("@")[-1])
    log.info("模型目录: %s，发现 %d 个模型", settings.models_dir, len(items))
    for m in items:
        log.info("  - %s [%s/%s] %s", m["id"], m["type"], m["kind"], m["status"])
    yield


app = FastAPI(title="AI 聊天对话系统 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(str(exc.detail), exc.status_code),
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    msg = f"参数错误：{first.get('loc', '')} {first.get('msg', '')}".strip()
    return JSONResponse(status_code=422, content=fail(msg, 422))


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    log.exception("未捕获异常")
    return JSONResponse(status_code=500, content=fail(f"服务器内部错误：{exc}", 500))


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(models.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"code": 0, "message": "ok", "data": {"status": "healthy"}}
