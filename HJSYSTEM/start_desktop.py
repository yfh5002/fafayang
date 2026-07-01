# -*- coding: utf-8 -*-
"""
HJSYSTEM PyQt6 Desktop Application 启动器
替代 start_desktop.bat - 检查环境并启动桌面应用
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()


def main():
    os.system("cls" if os.name == "nt" else "clear")

    print("=" * 50)
    print("  HJSYSTEM PyQt6 Desktop Application")
    print("=" * 50)
    print()

    # 检查 Python
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True, text=True, check=True
        )
        print(f"[Info] Found: {result.stdout.strip() or result.stderr.strip()}")
    except Exception:
        print("[Error] Python not found!")
        print("Please install Python 3.8+ and add to PATH")
        input("\n按 Enter 键退出...")
        sys.exit(1)

    print()

    # 检查 PyQt6
    try:
        import PyQt6  # noqa: F401
        print("[Info] PyQt6 已安装")
    except ImportError:
        print("[Info] 正在安装 PyQt6...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "PyQt6"],
            cwd=BASE_DIR
        )

    print()
    print("[Info] Starting HJSYSTEM Desktop Application...")
    print()

    # 启动桌面应用
    desktop_script = BASE_DIR / "desktop_app.py"
    if not desktop_script.exists():
        print(f"[Error] 未找到桌面应用脚本: {desktop_script}")
        input("\n按 Enter 键退出...")
        sys.exit(1)

    result = subprocess.run(
        [sys.executable, str(desktop_script)],
        cwd=BASE_DIR
    )

    if result.returncode != 0:
        print()
        print("[Error] Application failed to start!")
        print("[Info] Please check if all dependencies are installed:")
        print("  pip install -r requirements.txt")
        input("\n按 Enter 键退出...")


if __name__ == "__main__":
    main()
