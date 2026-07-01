# -*- coding: utf-8 -*-
"""
HJSYSTEM 用户认证系统
基于 JWT Token 的简单认证，支持首次自动创建默认管理员
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.database import get_db
from backend.models import User
from backend.config import settings

# ==================== 配置 ====================
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = settings.access_token_expire_days

# 默认管理员账户（首次启动自动创建）
DEFAULT_ADMIN = {"username": "admin", "password": "admin", "display_name": "管理员"}

# 密码哈希 - 使用sha256替代bcrypt以避免长度限制问题
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


# ==================== 密码工具 ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


# ==================== JWT Token ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT 访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码 JWT 令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ==================== 用户验证 ====================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    获取当前登录用户（可选认证，未登录返回 None）
    用于既支持游客访问、又支持登录后记录操作人的场景
    """
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    username = payload.get("sub")
    if not username:
        return None
    return db.query(User).filter(User.username == username).first()


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    强制认证 — 未登录返回 401
    用于必须登录才能访问的接口
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证信息无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(
    user: User = Depends(require_auth)
) -> User:
    """强制管理员权限"""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user


# ==================== 初始化 ====================

def init_default_admin(db: Session):
    """初始化默认管理员账户（如果不存在）"""
    existing = db.query(User).filter(User.username == DEFAULT_ADMIN["username"]).first()
    if not existing:
        user = User(
            username=DEFAULT_ADMIN["username"],
            password_hash=get_password_hash(DEFAULT_ADMIN["password"]),
            display_name=DEFAULT_ADMIN["display_name"],
            is_admin=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[Auth] 默认管理员已创建: {DEFAULT_ADMIN['username']} / {DEFAULT_ADMIN['password']}")
    else:
        print(f"[Auth] 管理员账户已存在: {DEFAULT_ADMIN['username']}")


def update_last_login(db: Session, user: User):
    """更新用户最后登录时间"""
    user.last_login = datetime.now()
    db.commit()
