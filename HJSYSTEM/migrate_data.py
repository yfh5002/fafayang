# -*- coding: utf-8 -*-
"""
HJSYSTEM Data Migration Script
Migrate data from HJKU.xlsx to SQLite database
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import init_db, SessionLocal
from backend.excel_handler import migrate_excel_to_db
from backend.crud import get_component_count


def migrate():
    """Migrate data from Excel to database"""
    excel_path = Path(__file__).parent / "HJKU.xlsx"
    
    if not excel_path.exists():
        print(f"[Error] Excel file not found: {excel_path}")
        print("[Info] Creating empty database...")
        init_db()
        return
    
    print(f"[Info] Found Excel file: {excel_path}")
    print("[Info] Initializing database...")
    init_db()
    
    print("[Info] Migrating data...")
    db = SessionLocal()
    try:
        imported, skipped = migrate_excel_to_db(str(excel_path), db)
        total = get_component_count(db)
        
        print(f"[Success] Migration complete!")
        print(f"  - Imported: {imported}")
        print(f"  - Skipped: {skipped}")
        print(f"  - Total in database: {total}")
        
    except Exception as e:
        print(f"[Error] Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
