# -*- coding: utf-8 -*-
"""
HJSYSTEM Backend Package
"""

from .database import init_db, get_db, engine, SessionLocal
from .models import Component, LogEntry, User
from .schemas import (
    ComponentCreate, ComponentUpdate, ComponentResponse,
    ComponentListResponse,
    LogCreateRequest, LogEntryResponse,
    ExcelImportResponse, ExcelExportRequest,
    PriceCalculationRequest, PriceCalculationResponse,
    SystemStatus, UserLoginRequest, UserLoginResponse,
)
from .auth import (
    create_access_token, verify_password, get_password_hash,
    get_current_user, require_auth, require_admin,
    init_default_admin, update_last_login,
)
from .crud import (
    get_component, get_components, create_component, update_component,
    delete_component, get_component_count, get_all_components,
    get_components_by_ids, delete_all_components, get_max_sequence,
    bulk_create_components, dedup_by_model,
    create_log_entry, get_logs, get_all_logs, clear_logs,
)
from .excel_handler import import_from_excel, export_to_excel
from .utils import (
    get_local_ips, get_pid_by_port, is_server_running,
    check_server_https_health, stop_server,
    parse_computer_name, BASE_DIR, CERT_DIR, LOG_DIR, DATA_DIR, SERVER_PORT,
)

__all__ = [
    # 数据库
    'init_db', 'get_db', 'engine', 'SessionLocal',
    # 模型
    'Component', 'LogEntry', 'User',
    # Schema
    'ComponentCreate', 'ComponentUpdate', 'ComponentResponse',
    'ComponentListResponse',
    'LogCreateRequest', 'LogEntryResponse',
    'ExcelImportResponse', 'ExcelExportRequest',
    'PriceCalculationRequest', 'PriceCalculationResponse',
    'SystemStatus', 'UserLoginRequest', 'UserLoginResponse',
    # Auth
    'create_access_token', 'verify_password', 'get_password_hash',
    'get_current_user', 'require_auth', 'require_admin',
    'init_default_admin', 'update_last_login',
    # CRUD - 元器件
    'get_component', 'get_components', 'create_component', 'update_component',
    'delete_component', 'get_component_count', 'get_all_components',
    'get_components_by_ids', 'delete_all_components', 'get_max_sequence',
    'bulk_create_components', 'dedup_by_model',
    # CRUD - 日志
    'create_log_entry', 'get_logs', 'get_all_logs', 'clear_logs',
    # Excel
    'import_from_excel', 'export_to_excel',
    # 工具
    'get_local_ips', 'get_pid_by_port', 'is_server_running',
    'check_server_https_health', 'stop_server',
    'parse_computer_name', 'BASE_DIR', 'CERT_DIR', 'LOG_DIR', 'DATA_DIR', 'SERVER_PORT',
]
