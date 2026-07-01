# -*- coding: utf-8 -*-
"""
HJSYSTEM CA 证书安装工具
替代 install-cert.bat - 安装 CA 证书到系统信任根存储
需要管理员权限运行
"""

import os
import sys
import subprocess
import ctypes
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
CERT_FILE = BASE_DIR / "certs" / "ca.crt"


def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_as_admin():
    """以管理员权限重新启动自身"""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, str(__file__), str(BASE_DIR), 1
    )


def main():
    if not is_admin():
        print("[错误] 需要管理员权限！")
        print()
        print("将尝试以管理员身份重新运行...")
        run_as_admin()
        sys.exit(0)

    print("=" * 50)
    print("  HJSYSTEM CA 证书安装工具")
    print("=" * 50)
    print()

    if not CERT_FILE.exists():
        print("[错误] 未找到 CA 证书文件！")
        print(f"证书路径: {CERT_FILE}")
        print()
        print("请先运行 start_python.py 中的 [1] Start Server 生成证书")
        input("\n按 Enter 键退出...")
        sys.exit(1)

    print(f"[信息] 证书文件: {CERT_FILE}")
    print()

    print("[步骤1/3] 安装 CA 证书到系统信任库...")
    try:
        result = subprocess.run(
            ["certutil", "-addstore", "-f", "Root", str(CERT_FILE)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[成功] CA 证书安装成功！")
        else:
            print("[错误] CA 证书安装失败！")
            print(result.stderr.strip())
            input("\n按 Enter 键退出...")
            sys.exit(1)
    except FileNotFoundError:
        print("[错误] certutil 命令未找到！")
        print("请确保 Windows 系统工具箱已安装。")
        input("\n按 Enter 键退出...")
        sys.exit(1)

    print()
    print("[步骤2/3] 清除浏览器缓存...")
    print("[提示] 请手动清除浏览器缓存或重启浏览器")
    print()

    print("[步骤3/3] 验证证书安装...")
    try:
        result = subprocess.run(
            ["certutil", "-store", "Root"],
            capture_output=True, text=True
        )
        if "HJSYSTEM" in result.stdout or "HJSYSTEM" in result.stderr:
            print("[成功] 证书验证成功！")
        else:
            print("[警告] 证书验证失败，请手动检查证书存储")
    except Exception:
        print("[警告] 证书验证遇到问题，请手动检查")

    print()
    print("=" * 50)
    print("安装完成！")
    print("=" * 50)
    print()
    print("请执行以下操作:")
    print("1. 重启浏览器")
    print("2. 访问 https://localhost:5002/HJ.html")
    print("3. 如果仍然显示不安全，请尝试清除浏览器缓存")
    print()
    input("按 Enter 键退出...")


if __name__ == "__main__":
    main()
