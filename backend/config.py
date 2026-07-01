# -*- coding: utf-8 -*-
"""
HJSYSTEM 统一配置管理
集中管理所有硬编码参数，支持环境变量覆盖
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# ==================== 基础路径 ====================
BASE_DIR = Path(__file__).parent.parent.resolve()
DATA_DIR = BASE_DIR / "data"
CERT_DIR = BASE_DIR / "certs"
LOG_DIR = BASE_DIR / "logs"
EXPORTS_DIR = BASE_DIR / "exports"
TEMP_DIR = BASE_DIR / "temp"
STATIC_DIR = BASE_DIR / "static"


class Settings(BaseSettings):
    """系统配置类 - 支持环境变量覆盖"""
    
    # 服务器配置
    server_host: str = "0.0.0.0"
    server_port: int = 5002
    app_title: str = "HJSYSTEM API"
    app_description: str = "元器件核价系统后端API"
    app_version: str = "2.0.0"
    
    # 安全配置
    secret_key: str = "hjsystem-secret-key-change-in-production"
    
    # 数据库配置
    database_url: str = f"sqlite:///{DATA_DIR / 'hjsystem.db'}"
    
    # CORS配置
    cors_origins: list = ["https://localhost:5002", "https://127.0.0.1:5002", "https://172.16.7.200:5002"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # JWT配置
    access_token_expire_days: int = 7
    
    # 分页/导出配置
    default_page_size: int = 1000
    max_page_size: int = 500000
    export_max_rows: int = 10000
    
    # Excel配置
    excel_title_font: str = "Times New Roman"
    excel_data_font: str = "Times New Roman"
    excel_title_size: int = 9
    excel_data_size: int = 9
    excel_max_col_width: int = 25
    excel_print_columns: str = "A:G"
    
    # 日志配置
    log_retention_days: int = 365
    log_level: str = "INFO"
    
    # 分页预览配置
    sheet_view_mode: str = "pageBreakPreview"
    
    # 健康检查配置
    health_check_timeout: int = 5
    
    
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# 创建配置实例
settings = Settings()

# ==================== 导出配置常量 ====================
SERVER_HOST = settings.server_host
SERVER_PORT = settings.server_port
APP_TITLE = settings.app_title
APP_DESCRIPTION = settings.app_description
APP_VERSION = settings.app_version
SECRET_KEY = settings.secret_key

# SSL证书配置
CERT_FILE = CERT_DIR / "cert.pem"
KEY_FILE = CERT_DIR / "key.pem"
CA_FILE = CERT_DIR / "ca.crt"

# API配置
CORS_ORIGINS = settings.cors_origins
CORS_ALLOW_CREDENTIALS = settings.cors_allow_credentials
CORS_ALLOW_METHODS = settings.cors_allow_methods
CORS_ALLOW_HEADERS = settings.cors_allow_headers

# 分页/导出配置
DEFAULT_PAGE_SIZE = settings.default_page_size
MAX_PAGE_SIZE = settings.max_page_size
EXPORT_MAX_ROWS = settings.export_max_rows

# 日志级别
LOG_LEVEL = settings.log_level


