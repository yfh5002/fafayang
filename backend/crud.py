# -*- coding: utf-8 -*-
"""
HJSYSTEM CRUD Operations
Create, Read, Update, Delete operations for database models
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional, Tuple
from backend.models import Component, LogEntry, User
from backend.schemas import ComponentCreate, ComponentUpdate, LogCreateRequest


# ==================== Component CRUD ====================

def get_component(db: Session, component_id: int) -> Optional[Component]:
    """Get single component by ID"""
    return db.query(Component).filter(Component.id == component_id).first()


def get_components(
    db: Session,
    skip: int = 0,
    limit: int = 1000,
    search: str = ""
) -> Tuple[List[Component], int]:
    """Get components with optional search and pagination"""
    query = db.query(Component)

    # Apply search filter
    if search:
        # 支持多关键词空格隔开，每个关键词在名称/型号/备注中任意匹配
        keywords = [k.strip() for k in search.split() if k.strip()]
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                search_pattern = f"%{keyword}%"
                keyword_conditions.append(
                    or_(
                        Component.name.ilike(search_pattern),
                        Component.model.ilike(search_pattern),
                        Component.remarks.ilike(search_pattern)
                    )
                )
            query = query.filter(and_(*keyword_conditions))

    # Apply pagination first to get the subset
    components = query.order_by(Component.sequence).offset(skip).limit(limit).all()

    # Get total count using a separate optimized query
    total = query.order_by(None).offset(None).limit(None).count()

    return components, total


def get_all_components(db: Session) -> List[Component]:
    """Get all components without pagination"""
    return db.query(Component).order_by(Component.sequence).all()


def get_components_count(db: Session) -> int:
    """Get total count of components"""
    return db.query(Component).count()


def get_components_by_ids(db: Session, ids: List[int]) -> List[Component]:
    """Get components by ID list"""
    return db.query(Component).filter(Component.id.in_(ids)).all()


def create_component(db: Session, component: ComponentCreate) -> Component:
    """Create new component - will be displayed at the top"""
    db_component = Component(**component.model_dump())
    db_component.calculate_subtotal()
    
    # 设置sequence为最小sequence-1，让新组件显示在最顶部
    min_seq = db.query(func.min(Component.sequence)).scalar()
    if min_seq is not None:
        db_component.sequence = min_seq - 1
    else:
        db_component.sequence = 0
    
    db.add(db_component)
    db.commit()
    db.refresh(db_component)
    
    return db_component


def create_components_batch(db: Session, components: List[ComponentCreate], batch_size: int = 100) -> int:
    """Batch create components for faster import"""
    total_created = 0
    
    for i in range(0, len(components), batch_size):
        batch = components[i:i + batch_size]
        db_components = []
        
        for comp in batch:
            db_comp = Component(**comp.model_dump())
            db_comp.calculate_subtotal()
            db_components.append(db_comp)
        
        db.add_all(db_components)
        db.flush()  # 批量flush，不立即commit
        total_created += len(batch)
    
    db.commit()
    return total_created


def update_component(
    db: Session, 
    component_id: int, 
    component_update: ComponentUpdate
) -> Optional[Component]:
    """Update existing component"""
    db_component = get_component(db, component_id)
    if not db_component:
        return None
    
    # Update fields
    update_data = component_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_component, field, value)
    
    # Recalculate subtotal
    db_component.calculate_subtotal()
    
    db.commit()
    db.refresh(db_component)
    
    return db_component


def delete_component(db: Session, component_id: int) -> bool:
    """Delete component by ID"""
    db_component = get_component(db, component_id)
    if not db_component:
        return False
    
    db.delete(db_component)
    db.commit()
    
    return True


def delete_all_components(db: Session) -> int:
    """Delete all components, return count"""
    count = db.query(Component).delete()
    db.commit()
    return count


def get_component_count(db: Session) -> int:
    """Get total component count"""
    return db.query(Component).count()


def get_max_sequence(db: Session) -> int:
    """Get the maximum sequence number currently in use"""
    result = db.query(func.max(Component.sequence)).scalar()
    return result or 0


def bulk_create_components(
    db: Session,
    components: List[ComponentCreate]
) -> tuple:
    """
    Bulk create components, return (created_count, skipped_count, duplicate_count)
    - Deduplicates by name+model
    - Auto-assigns sequence to maintain Excel row order, new imports appear at top
    """
    created_count = 0
    skipped_count = 0
    duplicate_count = 0

    # Get existing model values for dedup
    existing_records = db.query(Component.model).filter(
        Component.model != None, Component.model != ""
    ).all()
    existing_keys = set()
    for (model,) in existing_records:
        existing_keys.add(model)

    # Get min sequence for auto-assignment (new imports go to top)
    min_seq = db.query(func.min(Component.sequence)).scalar()
    if min_seq is None:
        min_seq = 0

    for idx, comp_data in enumerate(components):
        # Dedup by model: skip if same model already exists
        dedup_key = comp_data.model or ""
        if dedup_key and dedup_key in existing_keys:
            duplicate_count += 1
            continue

        db_component = Component(**comp_data.model_dump())

        # Auto-assign sequence: new imports get smaller sequence to appear at top
        # Excel first row gets smallest sequence
        if not db_component.sequence or db_component.sequence == 0:
            db_component.sequence = min_seq - len(components) + idx

        db_component.calculate_subtotal()
        db.add(db_component)
        created_count += 1

        # Track in dedup set to handle intra-batch duplicates
        if dedup_key:
            existing_keys.add(dedup_key)

    db.commit()
    return created_count, duplicate_count


def dedup_by_model(db: Session) -> int:
    """
    Deduplicate by model field only - keep one row per model value.
    Keeps the first (oldest) record, removes duplicates.
    Returns: number of deleted rows.
    """
    from sqlalchemy import and_
    
    # Find all model values that appear more than once
    duplicates = (
        db.query(Component.model)
        .filter(Component.model != None, Component.model != "")
        .group_by(Component.model)
        .having(func.count(Component.id) > 1)
        .all()
    )
    
    if not duplicates:
        return 0
    
    total_deleted = 0
    for (model,) in duplicates:
        # Get all records with this model, ordered by id (oldest first)
        records = (
            db.query(Component.id)
            .filter(Component.model == model)
            .order_by(Component.id.asc())
            .all()
        )
        
        # Keep the first one, delete the rest
        ids_to_keep = records[0][0]
        ids_to_delete = [r[0] for r in records[1:]]
        
        if ids_to_delete:
            deleted = (
                db.query(Component)
                .filter(Component.id.in_(ids_to_delete))
                .delete(synchronize_session=False)
            )
            total_deleted += deleted
    
    db.commit()
    return total_deleted


# ==================== Log CRUD ====================

def create_log_entry(
    db: Session, 
    log_data: LogCreateRequest,
    user_ip: str = "",
    user_agent: str = "",
    computer_name: str = "",
    username: str = ""
) -> LogEntry:
    """Create new log entry"""
    # Convert dict to LogCreateRequest if needed
    if isinstance(log_data, dict):
            # 支持从字典中提取参数（兼容旧的调用方式）
            if 'user_ip' in log_data:
                user_ip = log_data['user_ip'] or user_ip
                del log_data['user_ip']
            if 'user_agent' in log_data:
                user_agent = log_data['user_agent'] or user_agent
                del log_data['user_agent']
            if 'computer_name' in log_data:
                computer_name = log_data['computer_name'] or computer_name
                del log_data['computer_name']
            if 'username' in log_data:
                username = log_data['username'] or username
                del log_data['username']
            log_data = LogCreateRequest(**log_data)
    
    db_log = LogEntry(
        action=log_data.action,
        details=log_data.details,
        component_name=log_data.component_name,
        component_model=log_data.component_model,
        user_ip=user_ip,
        user_agent=user_agent,
        computer_name=computer_name,
        username=username
    )
    
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return db_log


def get_logs(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    action_filter: str = ""
) -> List[LogEntry]:
    """Get logs with pagination and optional action filter"""
    query = db.query(LogEntry)
    if action_filter:
        query = query.filter(LogEntry.action.like(f"%{action_filter}%"))
    return query.order_by(
        LogEntry.created_at.desc()
    ).offset(skip).limit(limit).all()


def get_all_logs(db: Session) -> List[LogEntry]:
    """Get all logs"""
    return db.query(LogEntry).order_by(LogEntry.created_at.desc()).all()


def clear_logs(db: Session) -> int:
    """Clear all logs, return deleted count"""
    count = db.query(LogEntry).delete()
    db.commit()
    return count


# ==================== User CRUD ====================

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, username: str, password_hash: str, display_name: str = None, is_admin: bool = False) -> User:
    """Create new user"""
    db_user = User(
        username=username,
        password_hash=password_hash,
        display_name=display_name or username,
        is_admin=is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_password(db: Session, user_id: int, new_password_hash: str) -> bool:
    """Update user password"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    user.password_hash = new_password_hash
    db.commit()
    return True


def update_user_last_login(db: Session, user_id: int) -> bool:
    """Update user last login time"""
    from datetime import datetime
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    user.last_login = datetime.now()
    db.commit()
    return True


def get_all_users(db: Session) -> list:
    """Get all users"""
    return db.query(User).order_by(User.created_at.desc()).all()


def delete_user(db: Session, user_id: int) -> bool:
    """Delete user by ID"""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
