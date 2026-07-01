# -*- coding: utf-8 -*-
"""
HJSYSTEM 共享工具函数
合并项目中所有重复的工具函数：IP检测、端口管理、DNS解析等
"""

import os
import re
import socket
import ssl
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from backend.config import BASE_DIR, CERT_DIR, LOG_DIR, DATA_DIR, SERVER_PORT

# ==================== IP 检测 ====================


def get_local_ips() -> list:
    """获取本机所有非回环 IPv4 地址（合并多种检测方式）"""
    ips = []

    # 方法1: ipconfig
    try:
        output = subprocess.check_output(
            ["ipconfig"], shell=True, text=True, encoding="utf-8", errors="replace"
        )
        for line in output.splitlines():
            if "IPv4" in line:
                ip = line.split(":")[-1].strip()
                if ip and ip not in ips and ip != "127.0.0.1":
                    ips.append(ip)
    except Exception:
        pass

    # 方法2: socket.getaddrinfo
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if (
                ip.count(".") == 3
                and not ip.startswith("127.")
                and ip not in ips
            ):
                ips.append(ip)
    except Exception:
        pass

    # 方法3: 遍历网络接口
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ip.count(".") == 3 and ip not in ips:
                ips.append(ip)
    except Exception:
        pass

    return ips


# ==================== 端口 / 进程管理 ====================


def get_pid_by_port(port: int = SERVER_PORT):
    """通过 netstat 查找指定端口正在监听的进程 PID"""
    try:
        output = subprocess.check_output(
            ["netstat", "-ano"], shell=True, text=True, encoding="utf-8"
        )
        pattern = rf":{port}\s+.*LISTENING\s+(\d+)"
        match = re.search(pattern, output)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None


def is_server_running(port: int = SERVER_PORT):
    """检查服务器是否在运行，返回 PID 或 None（结合端口检测 + API 健康检查）"""
    # 方法1: 端口检测
    pid = get_pid_by_port(port)
    if pid:
        return pid
    # 方法2: API 健康检查（端口可能被反向代理等场景）
    if check_server_https_health(port):
        return 0  # 用0表示"正在运行但PID未知"
    return None


def check_server_https_health(port: int = SERVER_PORT) -> bool:
    """通过 HTTPS API 检查服务器是否健康响应（多重检测）"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # 检测路径列表，按优先级排序
    paths = ["/api/status", "/"]
    for path in paths:
        try:
            req = urllib.request.Request(f"https://localhost:{port}{path}")
            resp = urllib.request.urlopen(req, context=ctx, timeout=5)
            if resp.status < 500:  # 200/301/302/404 都算服务在运行
                return True
        except urllib.error.HTTPError as e:
            if e.code < 500:  # 收到 HTTP 响应说明服务器在运行
                return True
        except Exception:
            continue
    return False


def _find_pid_by_port_fallback(port: int) -> Optional[int]:
    """通过更广泛的 netstat 匹配查找端口占用进程（包括非 LISTENING 状态）"""
    try:
        output = subprocess.check_output(
            ["netstat", "-ano"], shell=True, text=True, encoding="utf-8"
        )
        for line in output.splitlines():
            if f":{port}" in line:
                # 提取行末的 PID
                parts = line.strip().split()
                if parts and parts[-1].isdigit():
                    return int(parts[-1])
    except Exception:
        pass
    return None


def _taskkill_pid(pid: int) -> bool:
    """使用 taskkill 终止进程"""
    try:
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            capture_output=True, shell=True, check=True, timeout=5
        )
        return True
    except Exception:
        return False


def stop_server(port: int = SERVER_PORT) -> bool:
    """停止指定端口的服务器进程（多重查找 + 强力终止）"""
    # 方法1: 标准端口查找
    if get_pid_by_port(port) and _taskkill_pid(get_pid_by_port(port)):
        return True
    # 方法2: 宽泛匹配 netstat（含非 LISTENING 状态的行）
    fallback_pid = _find_pid_by_port_fallback(port)
    if fallback_pid and _taskkill_pid(fallback_pid):
        # 确认是否真的停掉了
        time.sleep(1)
        if not get_pid_by_port(port) and not _find_pid_by_port_fallback(port):
            return True
    # 方法3: 通过 PowerShell Get-NetTCPConnection 查找
    try:
        ps_cmd = f'Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess'
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            ps_pid = int(result.stdout.strip().split()[-1])
            return _taskkill_pid(ps_pid)
    except Exception:
        pass
    return False


# ==================== DNS 反向解析（异步 + 缓存）====================

# 模块级长驻线程池 + 缓存（避免每次创建/销毁线程池的开销）
_dns_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="dns")
_dns_cache: dict = {}
_dns_pending: dict = {}


def _dns_lookup(ip: str) -> str:
    """执行 DNS 反向查询（在线程池中运行）"""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""


def parse_computer_name(user_ip: str, user_agent: str = "") -> str:
    """
    解析电脑名称
    - 优先通过 DNS 反向解析获取主机名（异步 + 缓存，不阻塞调用）
    - 首次返回 IP，缓存命中后返回主机名
    - 本机/无 IP 时回退到 User-Agent 解析
    """
    if user_ip in _dns_cache:
        hostname = _dns_cache[user_ip]
        if hostname:
            return hostname

    # 提交异步 DNS 查询
    if user_ip and user_ip not in ("127.0.0.1", "::1", "localhost") and user_ip not in _dns_pending:
        _dns_pending[user_ip] = _dns_executor.submit(_dns_lookup, user_ip)

    # 尝试获取结果（非阻塞）
    if user_ip in _dns_pending:
        future = _dns_pending[user_ip]
        if future.done():
            hostname = future.result()
            _dns_cache[user_ip] = hostname
            del _dns_pending[user_ip]
            if hostname:
                return hostname
        return user_ip

    # 回退到 User-Agent 解析
    return _parse_ua_fallback(user_agent) if user_agent else "-"


def _parse_ua_fallback(user_agent: str) -> str:
    """从 User-Agent 解析操作系统/浏览器"""
    ua = user_agent.lower()
    os_parts = []
    if "windows nt 10.0" in ua:
        os_parts.append("Windows 10")
    elif "windows nt 6.3" in ua:
        os_parts.append("Windows 8.1")
    elif "windows nt 6.2" in ua:
        os_parts.append("Windows 8")
    elif "windows nt 6.1" in ua:
        os_parts.append("Windows 7")
    elif "windows" in ua:
        os_parts.append("Windows")
    elif "macintosh" in ua or "mac os" in ua:
        os_parts.append("macOS")
    elif "linux" in ua:
        os_parts.append("Linux")
    elif "android" in ua:
        os_parts.append("Android")
    elif "iphone" in ua or "ipad" in ua:
        os_parts.append("iOS")
    else:
        os_parts.append("Unknown OS")

    if "edg/" in ua:
        os_parts.append("Edge")
    elif "chrome/" in ua:
        os_parts.append("Chrome")
    elif "safari/" in ua and "chrome" not in ua:
        os_parts.append("Safari")
    elif "firefox/" in ua:
        os_parts.append("Firefox")
    elif "trident" in ua or "msie" in ua:
        os_parts.append("IE")

    return " / ".join(os_parts) if os_parts else "-"
