# -*- coding: utf-8 -*-
"""
HJSYSTEM V2.0 服务器管理脚本
替代 start_python.bat，复用 backend.utils 中的工具函数
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 确保项目根目录在 sys.path 中
_PROJECT_ROOT = str(Path(__file__).parent.resolve())
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _detect_venv_site_packages():
    """检测并返回 .venv/Lib/site-packages 的路径，若存在则加入 sys.path"""
    venv_path = Path(_PROJECT_ROOT) / ".venv"
    if not venv_path.exists():
        return None

    # Python venv 在 Windows 下的标准 site-packages 路径
    site_pkgs = venv_path / "Lib" / "site-packages"
    if site_pkgs.exists():
        sp = str(site_pkgs)
        if sp not in sys.path:
            sys.path.insert(0, sp)
        return sp

    # 兼容其他平台（以防迁移）
    alt = venv_path / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
    if alt.exists():
        sp = str(alt)
        if sp not in sys.path:
            sys.path.insert(0, sp)
        return sp

    return None


def _is_interactive():
    """判断当前是否处于交互式终端环境（是否能安全调用 input()）"""
    return sys.stdin is not None and hasattr(sys.stdin, "isatty") and sys.stdin.isatty()


def _safe_pause(message="\n按 Enter 键退出..."):
    """仅在交互式环境下暂停，避免非交互运行时 EOFError"""
    if _is_interactive():
        try:
            input(message)
        except (EOFError, OSError):
            pass


# ---------- 自动加载 .venv 的 site-packages ----------
_VENV_SP = _detect_venv_site_packages()

# ---------- 前置依赖检查 ----------
# 注意：python-jose 安装后的包名为 "jose"，其它为真实的 import name
_REQUIRED_DEPS = ("fastapi", "uvicorn", "sqlalchemy", "openpyxl", "jose", "passlib", "multipart")
_MISSING_DEPS = []
for _dep in _REQUIRED_DEPS:
    try:
        __import__(_dep)
    except ImportError:
        _MISSING_DEPS.append(_dep)

if _MISSING_DEPS:
    print("\n" + "=" * 50)
    print("  [Fatal Error] 缺少必要的 Python 依赖包")
    print("=" * 50)
    print(f"\n当前解释器: {sys.executable}")
    if _VENV_SP:
        print(f"已自动加载 venv site-packages: {_VENV_SP}")
    else:
        print("未发现可用的 .venv 虚拟环境（或缺少 python.exe/site-packages）")
    print("\n缺失的包:")
    for _dep in _MISSING_DEPS:
        print(f"  - {_dep}")
    print("\n请运行以下命令之一来安装依赖:")
    req_txt = Path(_PROJECT_ROOT) / "requirements.txt"
    if req_txt.exists():
        print(f'  python -m pip install -r "{req_txt}"')
    print("  python -m pip install python-jose[cryptography] passlib[bcrypt] fastapi uvicorn sqlalchemy openpyxl")
    print("\n（若已使用 .venv，请确认 venv 中安装过上述依赖；可通过 .venv\\Scripts\\pip.exe 安装）")
    _safe_pause()
    raise SystemExit(1)

try:
    from backend.utils import (
        BASE_DIR, LOG_DIR, CERT_DIR, SERVER_PORT,
        get_pid_by_port, is_server_running,
        check_server_https_health, stop_server, get_local_ips,
    )
    CERT_FILE = CERT_DIR / "cert.pem"
except Exception as _import_err:
    import traceback
    print("\n[Fatal Error] 模块导入失败，请检查 Python 版本及依赖:")
    print(str(_import_err))
    print("\n详细错误信息:")
    traceback.print_exc()
    _safe_pause()
    raise SystemExit(1)


def print_header():
    """打印应用标题"""
    print("=" * 50)
    print("  HJSYSTEM V2.0")
    print("=" * 50)
    print()


def check_python():
    """检查 Python 是否可用并打印版本"""
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True, text=True, check=True
        )
        print(f"[Info] Found: {result.stdout.strip() or result.stderr.strip()}")
        print()
        return True
    except Exception:
        print("[Error] Python not found!")
        return False


def check_certificates():
    """检查并生成 HTTPS 证书"""
    if CERT_FILE.exists():
        return True

    print("[Info] HTTPS certificate not found, generating...")
    gen_script = BASE_DIR / "generate-cert-python.py"
    if not gen_script.exists():
        print("[Error] Certificate generator not found!")
        return False

    result = subprocess.run([sys.executable, str(gen_script)], cwd=BASE_DIR, env=_child_python_env())
    if result.returncode != 0:
        print("[Error] Certificate generation failed!")
        return False

    print("[Success] Certificates generated!")
    if not CERT_FILE.exists():
        print("[Error] Certificates still not found after generation!")
        return False
    return True


def _print_access_urls():
    """打印访问地址"""
    print("=" * 50)
    print("  Access URLs (HTTPS):")
    print("=" * 50)
    print(f"  Local: https://localhost:{SERVER_PORT}/HJ.html")
    for ip in get_local_ips():
        print(f"  LAN:   https://{ip}:{SERVER_PORT}/HJ.html")
    print()
    print("[Tip] If showing 'Not Secure', run as admin: python install_cert.py")


def _start_server_background():
    """后台启动服务器进程"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # 清空旧日志，避免误读上次错误信息
    with open(LOG_DIR / "python_server.log", "w", encoding="utf-8"):
        pass
    with open(LOG_DIR / "python_server.log", "a", encoding="utf-8") as f:
        subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=BASE_DIR,
            stdout=f,
            stderr=subprocess.STDOUT,
            env=_child_python_env(),
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        )


def _force_free_port(port, max_wait=5):
    """强制释放被占用的端口"""
    import socket

    # 方法1: 通过 backend.utils 停止
    try:
        from backend.utils import stop_server, get_pid_by_port
        pid = get_pid_by_port(port)
        if pid:
            print(f"[Info] Killing PID {pid} occupying port {port}...")
            stop_server(port)
            time.sleep(1)
    except Exception:
        pass

    # 方法2: 直接用 netstat + taskkill
    for attempt in range(max_wait):
        # 检查端口是否已释放
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        if result != 0:  # 连接失败 = 端口空闲
            return True

        # 还被占用，尝试 taskkill 强杀
        try:
            r = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True, text=True, timeout=5
            )
            for line in r.stdout.splitlines():
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    old_pid = parts[-1]
                    print(f"[Info] Force killing PID {old_pid} on port {port}...")
                    subprocess.run(
                        ['taskkill', '/F', '/PID', old_pid],
                        capture_output=True, timeout=5
                    )
                    break
        except Exception:
            pass
        time.sleep(1)

    return False


def start_server():
    """启动服务器（含自动重试机制）"""
    print()
    print("[Info] Starting Python FastAPI server...")
    print(f"[Info] Port: {SERVER_PORT} (HTTPS only)")
    print()

    # 检查端口是否被占用
    pid = is_server_running()
    if pid:
        print(f"[Warning] Server already running on port {SERVER_PORT} (PID: {pid})!")
        print(f"[Info] Visit: https://localhost:{SERVER_PORT}/HJ.html")
        print()
        pause()
        return

    # 额外检查：端口是否被占用（即使 API 未响应）
    from backend.utils import get_pid_by_port
    occupied_pid = get_pid_by_port(SERVER_PORT)
    if occupied_pid:
        print(f"[Warning] Port {SERVER_PORT} is occupied by PID {occupied_pid}, releasing...")
        stop_server(SERVER_PORT)
        time.sleep(2)

    if not check_certificates():
        print("[Error] Server cannot start without HTTPS certificates.")
        pause()
        return

    # 启动并重试（最多2次）
    for attempt in range(2):
        _start_server_background()

        print("[Info] Waiting for server to start...")
        time.sleep(4)

        if check_server_https_health() or is_server_running():
            print("[Success] Server started!")
            print()
            _print_access_urls()
            print()
            pause()
            return

        # 首次失败：尝试强制释放端口后重试
        if attempt == 0:
            print("[Warning] Server failed to start (port may be occupied)...")
            print("[Info] Attempting to free port and retry...")
            if _force_free_port(SERVER_PORT):
                time.sleep(1)
                print("[Info] Retrying...")
                continue
            else:
                break

    print("[Error] Server failed to start after retries!")
    print(f"[Info] Check {LOG_DIR / 'python_server.log'} for details")
    # 尝试读取日志中的最后几行错误信息
    try:
        with open(LOG_DIR / "python_server.log", "r", encoding="utf-8") as f:
            lines = f.readlines()
            error_lines = [l.strip() for l in lines if 'ERROR' in l or 'Error' in l or 'error' in l]
            if error_lines:
                print("\n[Debug] Last errors:")
                for el in error_lines[-5:]:
                    print(f"  {el}")
    except Exception:
        pass
    pause()


def _stop_and_wait():
    """停止服务器并等待"""
    print(f"[Info] Step 1/2 - Stopping server (port {SERVER_PORT})...")
    if stop_server():
        time.sleep(2)
        return True
    return False


def restart_server():
    """重启服务器（含自动重试机制）"""
    print()
    print("[Info] Restarting server...")

    _stop_and_wait()

    # 确保端口完全释放
    time.sleep(1)
    _force_free_port(SERVER_PORT)

    print("[Info] Step 2/2 - Starting server...")
    if not CERT_FILE.exists():
        print("[Error] Certificates not found!")
        pause()
        return

    for attempt in range(2):
        _start_server_background()
        time.sleep(4)

        if check_server_https_health() or is_server_running():
            print("[Success] Server restarted!")
            print()
            _print_access_urls()
            print()
            pause()
            return

        if attempt == 0:
            print("[Warning] Restart failed, forcing port release and retrying...")
            _force_free_port(SERVER_PORT)
            time.sleep(1)

    print("[Error] Server failed to restart after retries!")
    print(f"[Info] Check {LOG_DIR / 'python_server.log'} for details")
    pause()


def migrate_data():
    """执行数据迁移（Excel to SQLite）"""
    print()
    print("[Info] Migrating Excel data to SQLite...")
    result = subprocess.run(
        [sys.executable, "migrate_data.py"],
        cwd=BASE_DIR, capture_output=True, text=True,
        env=_child_python_env()
    )
    if result.returncode == 0:
        print("[Success] Migration complete!")
    else:
        print("[Error] Migration failed!")
        print("[Info] Make sure HJKU.xlsx exists")
        if result.stderr:
            print(f"[Debug] {result.stderr.strip()}")
    print()
    pause()


def check_status():
    """检查服务器运行状态"""
    print()
    print("[Info] Checking server status...")
    if check_server_https_health():
        print("\n[Info] Server is RUNNING")
    else:
        pid = is_server_running()
        if pid:
            print("[Info] Server port is open but API not responding")
        else:
            print("[Info] Server is STOPPED")
    print()
    pause()


def _get_startup_shortcut_path():
    """获取开机自启动快捷方式路径"""
    startup_dir = os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
    )
    return startup_dir, os.path.join(startup_dir, "HJSYSTEM-Python.lnk")


def _create_shortcut_ps(target, args, work_dir, desc, shortcut_path):
    """通过 PowerShell 创建快捷方式（纯 Python 实现，不依赖 VBS 文件）"""
    ps_script = (
        f'$ws = New-Object -ComObject WScript.Shell;'
        f'$lnk = $ws.CreateShortcut("{shortcut_path}");'
        f'$lnk.TargetPath = "{target}";'
        f'$lnk.Arguments = "{args}";'
        f'$lnk.WorkingDirectory = "{work_dir}";'
        f'$lnk.Description = "{desc}";'
        f'$lnk.Save()'
    )
    result = subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True, text=True, timeout=10
    )
    return result.returncode == 0


def create_autostart():
    """管理开机自启动（创建/删除快捷方式）"""
    print()
    startup_dir, shortcut_path = _get_startup_shortcut_path()
    os.makedirs(startup_dir, exist_ok=True)
    hidden_script = BASE_DIR / "start_python_hidden.py"

    # 检查当前状态
    already_enabled = os.path.exists(shortcut_path)

    if already_enabled:
        print(f"[Info] 当前状态: 已开启开机自动启动")
        print(f"[Info] 快捷方式: {shortcut_path}")
        print()
        choice = input("输入 [1] 取消自动启动  [2] 返回菜单: ").strip()
        if choice == "1":
            try:
                os.remove(shortcut_path)
                print("[Success] 已取消开机自动启动")
            except Exception as e:
                print(f"[Error] 取消失败: {e}")
        print()
        pause()
        return

    print("[Info] 正在创建开机自动启动...")
    print(f"[Info] 启动脚本: {hidden_script}")
    print()

    if _create_shortcut_ps(
        target=sys.executable,
        args=str(hidden_script),
        work_dir=str(BASE_DIR),
        desc="HJSYSTEM Python Server Auto-start",
        shortcut_path=shortcut_path
    ):
        print("[Success] 开机自动启动已开启！")
        print("[Info] 下次开机时服务器将自动启动（隐藏窗口）")
    else:
        print("[Warning] 创建快捷方式失败，请手动操作：")
        print(f"  1. 按 Win+R 输入 shell:startup")
        print(f"  2. 创建 {sys.executable} 的快捷方式")
        print(f"  3. 参数添加: {hidden_script}")
    print()
    pause()


def autostart_status():
    """检查并返回开机自启动状态"""
    _, shortcut_path = _get_startup_shortcut_path()
    return os.path.exists(shortcut_path)



def pause():
    """暂停等待用户按键（仅在交互式终端下生效）"""
    _safe_pause("\n按 Enter 键继续...")


def _child_python_env():
    """
    构造启动子 Python 进程的环境变量，确保子进程也能访问 .venv 的依赖。
    返回可用于 subprocess 的 env 字典副本。
    """
    env = os.environ.copy()
    if _VENV_SP:
        existing = env.get("PYTHONPATH", "")
        if _VENV_SP not in existing.split(os.pathsep):
            env["PYTHONPATH"] = _VENV_SP + (os.pathsep + existing if existing else "")
    return env


def _auto_start_server_if_needed():
    """自动检测并启动服务器（如果未运行）"""
    print("[Info] Checking server status...")
    
    # 检查服务器是否正在运行
    pid = is_server_running()
    if pid:
        print(f"[Info] Server already running (PID: {pid})")
        print(f"[Info] Visit: https://localhost:{SERVER_PORT}/HJ.html")
        return True
    
    # 服务器未运行，自动启动
    print("[Info] Server not running, starting automatically...")
    
    if not check_certificates():
        print("[Error] Cannot start server: HTTPS certificates missing")
        return False
    
    # 检查端口是否被占用
    from backend.utils import get_pid_by_port
    occupied_pid = get_pid_by_port(SERVER_PORT)
    if occupied_pid:
        print(f"[Info] Port {SERVER_PORT} occupied by PID {occupied_pid}, releasing...")
        stop_server(SERVER_PORT)
        time.sleep(2)
    
    # 启动服务器
    _start_server_background()
    print("[Info] Waiting for server to start...")
    
    # 等待最多10秒
    for _ in range(10):
        time.sleep(1)
        if check_server_https_health() or is_server_running():
            print("[Success] Server started automatically!")
            print(f"[Info] Visit: https://localhost:{SERVER_PORT}/HJ.html")
            return True
    
    print("[Error] Server failed to start automatically!")
    return False


def main():
    """主菜单"""
    os.system("cls" if os.name == "nt" else "clear")
    print_header()

    if not check_python():
        pause()
        return

    # 自动检测并启动服务器（如果未运行）
    _auto_start_server_if_needed()
    print()

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print_header()

        pid = is_server_running()
        if pid is None:
            status = "已停止"
        elif pid == 0:
            status = "运行中 (API检测)"
        else:
            status = f"运行中 (PID: {pid})"

        auto = "已开启" if autostart_status() else "未开启"
        print(f"  服务器状态: {status}  |  开机自启: {auto}")
        print()

        print("  [1] Start Server")
        print("  [2] Stop Server")
        print("  [3] Restart Server")
        print("  [4] Migrate Data (Excel to SQLite)")
        print("  [5] Check Status")
        print("  [6] 开机自启设置")
        print("  [7] Exit")
        print()

        choice = input("Select option: ").strip()

        if choice == "1":
            start_server()
        elif choice == "2":
            print()
            print(f"[Info] Stopping Python server (port {SERVER_PORT})...")
            if stop_server():
                print("[Success] Server stopped!")
            else:
                print("[Info] No server running on port", SERVER_PORT)
            print()
            pause()
        elif choice == "3":
            restart_server()
        elif choice == "4":
            migrate_data()
        elif choice == "5":
            check_status()
        elif choice == "6":
            create_autostart()
        elif choice == "7":
            print("\n退出程序。")
            break
        else:
            print("\n无效选项，请重新选择。")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("\n[Fatal Error] 程序启动失败:")
        print(str(e))
        print("\n详细错误信息:")
        traceback.print_exc()
        input("\n按 Enter 键退出...")
