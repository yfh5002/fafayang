# -*- coding: utf-8 -*-
"""
HJSYSTEM 后台静默启动脚本
替代 start_python_hidden.vbs - 隐藏窗口启动服务器
用于 Windows 开机自启动
"""

import os
import sys
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

# ---------- 自动加载 .venv 的 site-packages ----------
def _detect_venv_site_packages():
    venv_path = BASE_DIR / ".venv"
    if not venv_path.exists():
        return None
    site_pkgs = venv_path / "Lib" / "site-packages"
    if site_pkgs.exists():
        sp = str(site_pkgs)
        if sp not in sys.path:
            sys.path.insert(0, sp)
        return sp
    return None

_VENV_SP = _detect_venv_site_packages()


def _child_python_env():
    env = os.environ.copy()
    if _VENV_SP:
        existing = env.get("PYTHONPATH", "")
        if _VENV_SP not in existing.split(os.pathsep):
            env["PYTHONPATH"] = _VENV_SP + (os.pathsep + existing if existing else "")
    return env


def _check_server_running(port):
    """检查服务器是否正在运行"""
    try:
        from backend.utils import is_server_running
        return is_server_running()
    except Exception:
        # 如果无法导入，使用简单的端口检查
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0


def _start_server(port):
    """启动服务器"""
    main_script = BASE_DIR / "main.py"
    log_file = BASE_DIR / "logs" / "python_server.log"

    # 确保日志目录存在
    (BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)

    # 清空旧日志
    with open(log_file, "w", encoding="utf-8"):
        pass

    # 后台静默启动（CREATE_NO_WINDOW = 0x08000000）
    with open(log_file, "a", encoding="utf-8") as f:
        subprocess.Popen(
            [sys.executable, str(main_script)],
            cwd=BASE_DIR,
            stdout=f,
            stderr=subprocess.STDOUT,
            env=_child_python_env(),
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        )

    # 等待服务器启动
    for _ in range(15):
        time.sleep(1)
        if _check_server_running(port):
            return True
    return False


def main():
    """以隐藏窗口方式启动服务器（带自动检测）"""
    # 获取端口号
    port = 8000  # 默认端口
    try:
        from backend.utils import SERVER_PORT
        port = SERVER_PORT
    except Exception:
        pass

    # 检查服务器是否已运行
    if _check_server_running(port):
        return  # 服务器已运行，直接退出

    # 服务器未运行，启动服务器
    _start_server(port)


if __name__ == "__main__":
    main()