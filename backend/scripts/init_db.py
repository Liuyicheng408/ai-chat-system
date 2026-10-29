"""建库建表（MySQL 不存在时先建库，再交给 SQLAlchemy 建表）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, engine  # noqa: E402

url = settings.database_url
if url.startswith("mysql"):
    server_url = url.rsplit("/", 1)[0]
    db_name = url.rsplit("/", 1)[1].split("?")[0]
    tmp = create_engine(server_url, isolation_level="AUTOCOMMIT")
    with tmp.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    tmp.dispose()
    print(f"数据库 {db_name} 就绪")

import app.models  # noqa: E402,F401

Base.metadata.create_all(bind=engine)
print("表结构创建完成")
