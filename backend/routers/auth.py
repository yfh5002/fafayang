# -*- coding: utf-8 -*-
"""
用户认证路由
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import get_db
from backend.auth import (
    create_access_token, verify_password, get_current_user, require_auth,
    require_admin, update_last_login
)
from backend.crud import get_user_by_username, create_user as crud_create_user, update_user_password, get_all_users, delete_user, create_log_entry
from backend.auth import get_password_hash
from backend.schemas import UserLoginRequest, UserLoginResponse, UserResponse, UserCreate as UserCreateRequest
from backend.models import User
from backend.utils import parse_computer_name

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UserLoginResponse)
async def login(
    request: Request,
    login_data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = get_user_by_username(db, login_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 更新最后登录时间
    update_last_login(db, user)

    # 获取客户端信息
    user_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")

    # 记录登录日志
    create_log_entry(db, {
        "action": "login",
        "details": f"用户登录: {user.username}",
        "user_ip": user_ip,
        "user_agent": user_agent,
        "computer_name": parse_computer_name(user_ip, user_agent),
        "username": user.username
    })

    # 创建访问令牌
    access_token = create_access_token(data={"sub": user.username})

    return UserLoginResponse(
        success=True,
        token=access_token,
        username=user.username,
        display_name=user.display_name or user.username,
        is_admin=user.is_admin,
        message="登录成功"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user = Depends(get_current_user)
):
    """获取当前登录用户信息"""
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name or user.username,
        is_admin=user.is_admin,
        last_login=user.last_login.isoformat() if user.last_login else None
    )


@router.post("/register")
async def register(
    request: Request,
    user_data: UserCreateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """注册新用户（需要管理员权限）"""
    # 检查是否已存在
    existing = get_user_by_username(db, user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建用户
    password_hash = get_password_hash(user_data.password)
    user = crud_create_user(
        db=db,
        username=user_data.username,
        password_hash=password_hash,
        display_name=user_data.display_name,
        is_admin=user_data.is_admin
    )
    
    return {"success": True, "message": "用户创建成功"}


@router.put("/password")
async def change_password(
    request: Request,
    current_password: str,
    new_password: str,
    user = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """修改密码"""
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码错误")
    
    update_user_password(db, user.id, new_password)
    
    return {"success": True, "message": "密码修改成功"}


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（管理员）"""
    users = get_all_users(db)
    return [UserResponse(
        id=u.id,
        username=u.username,
        display_name=u.display_name or u.username,
        is_admin=u.is_admin,
        last_login=u.last_login.isoformat() if u.last_login else None
    ) for u in users]


@router.delete("/users/{user_id}")
async def remove_user(
    user_id: int,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除用户（管理员）"""
    # 不能删除自己
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"success": True, "message": "用户删除成功"}
