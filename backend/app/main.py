"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services import init_db
from app.routers import knowledge_bases, documents, qa


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化数据库，关闭时清理"""
    init_db()
    yield


app = FastAPI(
    title="SmartKB - 智能知识库问答系统",
    description="上传文档，AI 自动学习并智能回答",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS：允许飞书妙搭前端和本地开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(knowledge_bases.router)
app.include_router(documents.router)
app.include_router(qa.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": app.version}
