"""数据库连接管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# 开发环境使用 SQLite，生产使用 PostgreSQL
if settings.app_env == "production" and settings.supabase_url:
    db_url = settings.supabase_url.replace("https://", "postgresql://")
else:
    import os
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data.db")
    db_url = f"sqlite:///{db_path}"

engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表"""
    from app.models import Base
    Base.metadata.create_all(bind=engine)
