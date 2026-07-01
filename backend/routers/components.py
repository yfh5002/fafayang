# -*- coding: utf-8 -*-
"""
元器件管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.models import Component, User
from backend.auth import require_admin
from backend.crud import (
    get_components, get_component, create_component, update_component,
    delete_component, delete_all_components, get_component_count,
    get_components_by_ids, bulk_create_components, create_log_entry,
    dedup_by_model, create_components_batch
)
from backend.schemas import (
    ComponentCreate, ComponentUpdate, ComponentResponse, ComponentListResponse,
    ExcelImportResponse
)
from backend.excel_handler import import_from_excel
from backend.utils import parse_computer_name

router = APIRouter(prefix="/api/components", tags=["components"])


@router.get("", response_model=ComponentListResponse)
async def list_components(
    page: int = 1,
    page_size: int = 1000,
    search: str = "",
    db: Session = Depends(get_db)
):
    """获取元器件列表（分页+搜索）"""
    skip = (page - 1) * page_size
    if page_size > 500000:
        page_size = 500000
    components, total = get_components(db, skip=skip, limit=page_size, search=search)
    
    return ComponentListResponse(
        total=total,
        items=[ComponentResponse.model_validate(c) for c in components]
    )


@router.get("/{component_id}", response_model=ComponentResponse)
async def get_component_detail(component_id: int, db: Session = Depends(get_db)):
    """获取单个元器件详情"""
    component = get_component(db, component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return ComponentResponse.model_validate(component)


@router.post("", response_model=ComponentResponse)
async def add_component(
    request: Request,
    component: ComponentCreate,
    db: Session = Depends(get_db)
):
    """创建新元器件"""
    db_component = create_component(db, component)
    
    # 记录日志
    user_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")
    create_log_entry(db, {
        "action": "create",
        "details": f"创建元器件: {component.name}",
        "component_name": component.name,
        "component_model": component.model,
        "user_ip": user_ip,
        "user_agent": user_agent,
        "computer_name": parse_computer_name(user_ip, user_agent)
    })
    
    return ComponentResponse.model_validate(db_component)


@router.put("/{component_id}", response_model=ComponentResponse)
async def modify_component(
    request: Request,
    component_id: int,
    component_update: ComponentUpdate,
    db: Session = Depends(get_db)
):
    """更新元器件"""
    db_component = update_component(db, component_id, component_update)
    if not db_component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    # 记录日志
    user_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")
    create_log_entry(db, {
        "action": "update",
        "details": f"更新元器件: {db_component.name}",
        "component_name": db_component.name,
        "component_model": db_component.model,
        "user_ip": user_ip,
        "user_agent": user_agent,
        "computer_name": parse_computer_name(user_ip, user_agent)
    })
    
    return ComponentResponse.model_validate(db_component)


@router.delete("/{component_id}")
async def remove_component(
    request: Request,
    component_id: int,
    db: Session = Depends(get_db)
):
    """删除元器件"""
    component = get_component(db, component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    component_name = component.name
    component_model = component.model
    
    success = delete_component(db, component_id)
    if not success:
        raise HTTPException(status_code=500, detail="Delete failed")
    
    # 记录日志
    user_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")
    create_log_entry(db, {
        "action": "delete",
        "details": f"删除元器件: {component_name}",
        "component_name": component_name,
        "component_model": component_model,
        "user_ip": user_ip,
        "user_agent": user_agent,
        "computer_name": parse_computer_name(user_ip, user_agent)
    })
    
    return {"success": True, "message": "Component deleted"}


@router.delete("")
async def clear_all_components(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """清空所有元器件（需要管理员权限）"""
    count = get_component_count(db)
    delete_all_components(db)
    
    # 记录日志
    user_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")
    create_log_entry(db, {
        "action": "clear",
        "details": f"清空所有元器件，共 {count} 条",
        "user_ip": user_ip,
        "user_agent": user_agent,
        "computer_name": parse_computer_name(user_ip, user_agent),
        "username": current_user.username
    })
    
    return {"success": True, "count": count}


@router.post("/batch")
async def get_components_batch(
    request: dict,
    db: Session = Depends(get_db)
):
    """批量获取元器件（用于预览选中功能）"""
    ids = request.get('ids', [])
    # 转换为整数列表
    int_ids = [int(id) for id in ids if str(id).isdigit()]
    components = get_components_by_ids(db, int_ids)
    return [ComponentResponse.model_validate(c) for c in components]


@router.post("/import")
async def import_components(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """导入Excel元器件数据（优化版，支持批量插入）"""
    try:
        # 1. 读取Excel文件
        import_result = import_from_excel(file.file)
        components = import_result[0]
        skipped = import_result[1] if len(import_result) > 1 else 0
        
        total_count = len(components)
        
        # 2. 使用批量插入（每次100条，显著提高速度）
        if total_count > 0:
            created_count = create_components_batch(db, components, batch_size=100)
        else:
            created_count = 0
        
        # 记录日志
        user_ip = request.client.host if request.client else ""
        user_agent = request.headers.get("user-agent", "")
        create_log_entry(db, {
            "action": "import",
            "details": f"导入元器件: {created_count} 条成功, {skipped} 条跳过",
            "user_ip": user_ip,
            "user_agent": user_agent,
            "computer_name": parse_computer_name(user_ip, user_agent)
        })
        
        return ExcelImportResponse(
            success=True,
            message=f"导入成功，新增 {created_count} 条记录，跳过 {skipped} 条",
            imported=created_count,
            skipped=skipped
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/match-price")
async def match_price(
    request: Request,
    db: Session = Depends(get_db)
):
    """根据名称/型号/备注匹配价格"""
    body = await request.json()
    name = body.get('name', '').strip().lower()
    model = body.get('model', '').strip().lower()
    remarks = body.get('remarks', '').strip().lower()
    
    # 构建查询条件
    query = db.query(Component)
    conditions = []
    
    if name:
        conditions.append(Component.name.ilike(f'%{name}%'))
    if model:
        conditions.append(Component.model.ilike(f'%{model}%'))
    if remarks:
        conditions.append(Component.remarks.ilike(f'%{remarks}%'))
    
    if conditions:
        from sqlalchemy import or_
        query = query.filter(or_(*conditions))
    
    # 按匹配度排序
    components = query.limit(10).all()
    
    # 计算匹配分数，返回最匹配的一个
    best_match = None
    best_score = 0
    
    for comp in components:
        score = 0
        comp_name = (comp.name or '').lower()
        comp_model = (comp.model or '').lower()
        comp_remarks = (comp.remarks or '').lower()
        
        if name and comp_name:
            if name in comp_name or comp_name in name:
                score += 3
            elif any(n in comp_name for n in name.split()):
                score += 2
        if model and comp_model:
            if model in comp_model or comp_model in model:
                score += 3
            elif any(m in comp_model for m in model.split()):
                score += 2
        if remarks and comp_remarks:
            if remarks in comp_remarks or comp_remarks in remarks:
                score += 2
        
        if score > best_score:
            best_score = score
            best_match = comp
    
    if best_match and best_score >= 2:
        return {
            "success": True,
            "matched": True,
            "price": best_match.unit_price or 0,
            "name": best_match.name,
            "model": best_match.model
        }
    
    return {"success": True, "matched": False, "price": 0}


@router.post("/dedup")
async def deduplicate_components(
    request: Request,
    db: Session = Depends(get_db)
):
    """按型号去重"""
    removed_count = dedup_by_model(db)
    
    # 记录日志
    create_log_entry(db, {
        "action": "dedup",
        "details": f"去重完成，移除 {removed_count} 条重复记录",
        "user_ip": request.client.host if request.client else None
    })
    
    # 获取剩余数据数量
    from backend.crud import get_components_count
    remaining_count = get_components_count(db)
    
    return {"success": True, "deleted": removed_count, "remaining": remaining_count}
