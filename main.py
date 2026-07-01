# -*- coding: utf-8 -*-
"""
HJSYSTEM FastAPI Backend
Main application entry point
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

# Add backend to path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, Request, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import run

from backend.database import init_db, get_db
from backend.config import (
    SERVER_HOST, SERVER_PORT, APP_TITLE, APP_DESCRIPTION, APP_VERSION,
    CORS_ORIGINS, CORS_ALLOW_CREDENTIALS, CORS_ALLOW_METHODS, CORS_ALLOW_HEADERS,
    CERT_FILE, KEY_FILE
)
from backend.routers import components, auth, system
from backend.logger import app_logger


# 在线统计超时时间（秒）
ONLINE_TIMEOUT = 90  # 90秒无活动视为离线


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    app_logger.info("Initializing database...")
    init_db()
    app_logger.info("Database initialized")
    
    yield
    app_logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan
)

# Online users tracking middleware — 已废弃，统计逻辑改为数据库查询
# 保留空中间件以兼容现有代码，实际统计在 /api/status 中直接查询数据库
@app.middleware("http")
async def track_online_users(request: Request, call_next):
    response = await call_next(request)
    return response

# CORS middleware - 限制为配置的来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Register routers
app.include_router(components.router)
app.include_router(auth.router)
app.include_router(system.router)


# Root endpoint - redirect to login page
@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login.html", status_code=302)


# System status endpoint (used by frontend for online users & component count)
@app.get("/api/status")
async def status(db = Depends(get_db)):
    from backend.crud import get_component_count
    from backend.models import User
    from datetime import datetime, timedelta

    # 直接查询数据库：最近90秒内有心跳记录的用户数
    # 使用 last_login 字段作为在线判断依据（心跳时会更新）
    timeout = datetime.now() - timedelta(seconds=ONLINE_TIMEOUT)
    active_count = db.query(User).filter(User.last_login >= timeout).count()

    return {
        "status": "ok",
        "version": APP_VERSION,
        "online_users": active_count,
        "total_components": get_component_count(db)
    }


# Heartbeat endpoint for accurate online user tracking
@app.post("/api/heartbeat")
async def heartbeat(request: Request, db = Depends(get_db)):
    """前端心跳上报接口，用于维持在线状态
    更新用户最后活跃时间到数据库，/api/status 直接查询数据库统计在线人数
    """
    from backend.models import User
    from datetime import datetime

    # 从 Authorization 头解析 token，获取登录用户名
    auth_header = request.headers.get('authorization', '')
    username = None
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        from backend.auth import decode_token
        payload = decode_token(token)
        if payload:
            username = payload.get('sub')

    # 未登录用户不计入在线统计
    if not username:
        return {"success": False, "error": "未登录"}, 401

    # 更新用户最后活跃时间（用于在线统计）
    user = db.query(User).filter(User.username == username).first()
    if user:
        user.last_login = datetime.now()
        db.commit()

    return {"success": True}

# Login endpoint alias for frontend compatibility
@app.post("/api/login")
async def login_alias(request: Request, login_data: dict):
    # Forward to auth router
    from backend.routers.auth import login as auth_login
    from backend.database import get_db
    from backend.schemas import UserLoginRequest
    
    db = next(get_db())
    login_request = UserLoginRequest(**login_data)
    return await auth_login(request, login_request, db)

# User info endpoint alias for frontend compatibility
@app.get("/api/user")
async def user_info_alias(request: Request):
    # Get token from Authorization header
    auth_header = request.headers.get('authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        
        try:
            # Decode token and get user
            from backend.auth import decode_token
            from backend.database import get_db
            from backend.models import User
            
            payload = decode_token(token)
            if payload:
                username = payload.get("sub")
                if username:
                    db = next(get_db())
                    user = db.query(User).filter(User.username == username).first()
                    if user:
                        return {
                            'logged_in': True,
                            'user': {
                                'username': user.username,
                                'display_name': user.display_name or user.username,
                                'is_admin': user.is_admin
                            }
                        }
        except Exception:
            pass
    
    return {'logged_in': False}


# Import endpoint alias for frontend compatibility
@app.post("/api/import")
async def import_alias(request: Request, file: UploadFile = File(...)):
    # Forward to components router
    from backend.routers.components import import_components
    from backend.database import get_db
    
    db = next(get_db())
    return await import_components(request, file, db)


# Export backup endpoint alias for frontend compatibility
@app.post("/api/export-backup")
async def export_backup_alias(request: Request):
    # Forward to system router
    from backend.routers.system import export_components
    from backend.database import get_db
    from backend.schemas import ExcelExportRequest
    
    body = await request.json()
    db = next(get_db())
    title = body.get('title', '备份数据库')
    return await export_components(ExcelExportRequest(title=title), db)


# Export to file endpoint alias for frontend compatibility
@app.post("/api/export-to-file")
async def export_to_file_alias(request: Request):
    # Forward to system router
    from backend.routers.system import export_components, export_custom_data
    from backend.database import get_db
    from backend.schemas import ExcelExportRequest
    from backend.utils import parse_computer_name
    
    body = await request.json()
    db = next(get_db())
    
    # 获取客户端信息用于日志
    user_ip = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")
    computer_name = parse_computer_name(user_ip, user_agent)
    
    # 如果有自定义数据，使用自定义导出接口
    if 'data' in body and body['data'] and len(body['data']) > 0:
        return await export_custom_data(body, db, user_ip, user_agent, computer_name)
    
    # 否则使用数据库导出接口
    title = body.get('title', '元器件报价清单')
    return await export_components(ExcelExportRequest(title=title), db, user_ip, user_agent, computer_name)


# Static files
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 使用绝对路径
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Serve HTML files for direct access
@app.get("/HJ.html")
async def hj_html():
    return FileResponse(str(STATIC_DIR / "HJ.html"))

@app.get("/login/login.html")
async def login_html():
    return FileResponse(str(STATIC_DIR / "login.html"))

@app.get("/cert-download.html")
async def cert_download_html():
    return FileResponse(str(STATIC_DIR / "cert-download.html"))

# Catch-all for static files (fallback)
@app.get("/{path:path}")
async def catch_all(path: str):
    # Check if file exists in static directory
    file_path = STATIC_DIR / path
    if file_path.exists():
        return FileResponse(str(file_path))
    # Also check for direct HTML files
    html_path = STATIC_DIR / f"{path}.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"detail": "Not Found"}, 404


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    app_logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {"error": str(exc)}, 500


if __name__ == "__main__":
    # 优先使用 HTTPS（需要证书文件）
    # 添加超时配置，支持大模型长时间响应
    import os
    
    ssl_args = {}
    if CERT_FILE.exists() and KEY_FILE.exists():
        ssl_args = {
            "ssl_keyfile": str(KEY_FILE),
            "ssl_certfile": str(CERT_FILE)
        }
        print(f"[Info] Starting HTTPS server on port {SERVER_PORT}")
    else:
        print(f"[Warning] SSL certificates not found, falling back to HTTP")
    
    run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=False,
        log_level="info",
        timeout_keep_alive=600,  # 保持连接超时10分钟
        timeout_graceful_shutdown=600,  # 优雅关闭超时10分钟
        **ssl_args
    )
