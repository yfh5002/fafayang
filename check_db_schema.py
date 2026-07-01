# -*- coding: utf-8 -*-
"""
数据库表结构检查与修复脚本
检查 components 表是否包含 model, unit_price, subtotal, remarks 等字段
如缺少则自动添加
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from backend.database import engine, init_db
from backend.utils import DATA_DIR

DB_PATH = DATA_DIR / "hjsystem.db"


def check_and_fix_schema():
    """检查并修复数据库表结构"""
    if not DB_PATH.exists():
        print(f"[Error] 数据库文件不存在: {DB_PATH}")
        return

    # 确保所有模型已注册
    init_db()

    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("components")}
    print(f"[Info] 当前 components 表字段: {sorted(columns)}")

    required_columns = {
        "model": "VARCHAR(500)",
        "unit_price": "FLOAT DEFAULT 0.0",
        "subtotal": "FLOAT DEFAULT 0.0",
        "remarks": "VARCHAR(500)",
    }

    missing = []
    for col, col_type in required_columns.items():
        if col not in columns:
            missing.append(col)
            try:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE components ADD COLUMN {col} {col_type}"))
                    conn.commit()
                print(f"[Fix] 已添加缺失字段: {col} ({col_type})")
            except Exception as e:
                print(f"[Error] 添加字段 {col} 失败: {e}")

    if not missing:
        print("[OK] 所有必需字段均已存在，无需修复。")
    else:
        print("[OK] 数据库结构修复完成，请重启后端服务。")

    # 打印前5条数据，确认字段内容
    try:
        from backend.models import Component
        from backend.database import SessionLocal
        db = SessionLocal()
        try:
            rows = db.query(Component).limit(5).all()
            if rows:
                print("\n[Info] 数据库前5条数据样例:")
                for r in rows:
                    print(f"  id={r.id}, name={r.name}, model={r.model}, unit_price={r.unit_price}, subtotal={r.subtotal}, remarks={r.remarks}")
            else:
                print("\n[Info] 数据库中暂无数据。")
        finally:
            db.close()
    except Exception as e:
        print(f"[Error] 查询数据失败: {e}")


if __name__ == "__main__":
    check_and_fix_schema()
