# -*- coding: utf-8 -*-
"""
HJSYSTEM Database Configuration
SQLite database with SQLAlchemy ORM
"""

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os

# Database file path
BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = BASE_DIR / "data" / "hjsystem.db"

# Ensure data directory exists
DATABASE_PATH.parent.mkdir(exist_ok=True)

# SQLite URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,  # Set to True for SQL logging
)

# Enable foreign keys
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_table_schema(db):
    """检查并修复表结构（处理旧版数据库缺少列的问题）"""
    from backend.models import User as UserModel
    inspector = inspect(engine)

    # 检查 users 表是否需要修复
    if "users" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("users")}
        needed_cols = set(UserModel.__table__.columns.keys())
        if not needed_cols.issubset(existing_cols):
            print(f"[Database] users 表结构不完整，正在重建...")
            db.execute(text("DROP TABLE IF EXISTS users"))
            db.commit()

def init_db():
    """Initialize database - create all tables"""
    from backend.models import Component, LogEntry, User
    Base.metadata.create_all(bind=engine)
    print(f"[Database] Initialized at {DATABASE_PATH}")

    # 修复可能损坏的表结构
    db = SessionLocal()
    try:
        _ensure_table_schema(db)
        # 确保所有表都创建完成
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        import traceback
        print(f"[Database] 表结构修复失败: {e}")
        traceback.print_exc()
    finally:
        db.close()

    # 初始化默认管理员
    db = SessionLocal()
    try:
        from backend.auth import init_default_admin
        init_default_admin(db)
    except Exception as e:
        import traceback
        print(f"[Database] 初始化默认管理员失败: {e}")
        traceback.print_exc()
    finally:
        db.close()
