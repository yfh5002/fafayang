import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import time
import subprocess
import re
import socket
from queue import Queue
import ctypes
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor

# 隐藏控制台窗口（仅隐藏，不关闭进程）
try:
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
except:
    pass

# ==================== 外网探测目标池（预解析IP，避免DNS依赖） ====================
# 分为三类检测目标：TCP直连IP / HTTP验证(IP:端口) / DNS查询端口
# 多目标、多运营商冗余，提高检测可靠性
CHECK_TARGETS = [
    # TCP直连目标 (IP, 端口, 策略类型) —— 多个运营商冗余
    ("180.101.49.11", 443, "tcp"),      # 百度 HTTPS (电信)
    ("180.101.49.12", 443, "tcp"),      # 百度 HTTPS 备用IP
    ("110.242.68.66", 443, "tcp"),      # 百度 HTTPS (联通)
    ("1.1.1.1", 443, "tcp"),            # Cloudflare DNS
    ("8.8.8.8", 443, "tcp"),            # Google DNS
    ("223.5.5.5", 80, "tcp"),           # 阿里DNS
    ("119.29.29.29", 80, "tcp"),        # 腾讯DNS (DNSPod)
    ("14.215.177.38", 80, "tcp"),       # 百度 HTTP
    ("14.215.177.39", 80, "tcp"),       # 百度 HTTP 备用
    ("61.135.169.121", 80, "tcp"),      # 百度 HTTP (联通)
    ("20.205.243.166", 443, "tcp"),     # GitHub
]

# HTTP状态码验证目标 (IP, 端口)
HTTP_CHECK_TARGETS = [
    ("180.101.49.11", 80),   # 百度 HTTP
    ("14.215.177.38", 80),   # 百度 HTTP
    ("110.242.68.66", 80),   # 百度 HTTP 联通
    ("61.135.169.121", 80),  # 百度 HTTP 联通备用
]

# DNS探测目标服务器 (IP, 端口53) —— 国内外冗余
DNS_SERVERS = [
    "8.8.8.8",         # Google DNS
    "1.1.1.1",         # Cloudflare DNS
    "223.5.5.5",        # 阿里DNS
    "119.29.29.29",     # 腾讯DNS (DNSPod)
    "114.114.114.114",  # 114DNS
    "180.76.76.76",     # 百度DNS
]

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_admin():
    """非管理员时自动以管理员权限重新启动自身"""
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            '"{0}"'.format(sys.argv[0]), None, 1
        )
        sys.exit(0)

class NetChecker:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1400x750")
        self.root.title("内网设备扫描检测工具")
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        self.total_online = 0
        self.ip_internet_sorted = []
        self.ip_lan_only_sorted = []
        self.save_file_path = r"C:\Users\Administrator\Desktop\内网设备报告.txt"
        self.is_scanning = False
        self.task_queue = Queue(maxsize=255)
        self.worker_thread_num = 30

        # 网络配置（外网检测规格）
        self.subnet_mask = "255.255.255.0"
        self.dns_server = "202.101.172.35"
        self.gateway_ip = "172.16.4.254"  # 默认，根据输入IP第三段自动更新
        self.backup_dns = "8.8.8.8"        # 备用DNS固定

        self.create_widgets()

    def create_widgets(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=12, pady=10)

        tk.Label(top_frame, text="输入网段或固定IP：", font=("微软雅黑",11)).pack(side="left")
        self.ip_input = tk.Entry(top_frame, font=("Consolas",11), width=26)
        self.ip_input.pack(side="left", padx=8)
        self.ip_input.insert(0, "172.16.4.7")
        self.ip_input.bind("<KeyRelease>", self.on_ip_input_change)

        self.scan_btn = tk.Button(
            top_frame, text="开始扫描内网", font=("微软雅黑",11),
            command=self.start_scan_task, width=12
        )
        self.scan_btn.pack(side="left", padx=6)

        export_btn = tk.Button(
            top_frame, text="导出TXT报告", font=("微软雅黑",11),
            command=self.export_txt_report, width=12
        )
        export_btn.pack(side="left", padx=6)

        # 网络配置信息栏
        netcfg_frame = tk.Frame(self.root)
        netcfg_frame.pack(fill="x", padx=12, pady=(0, 6))

        tk.Label(netcfg_frame, text="子网掩码：", font=("微软雅黑", 9), fg="#555").pack(side="left")
        self.lbl_subnet = tk.Label(netcfg_frame, text=self.subnet_mask,
                                   font=("Consolas", 9, "bold"), fg="#1565C0")
        self.lbl_subnet.pack(side="left", padx=(2, 20))

        tk.Label(netcfg_frame, text="网关：", font=("微软雅黑", 9), fg="#555").pack(side="left")
        self.gateway_input = tk.Entry(netcfg_frame, font=("Consolas", 9), width=15)
        self.gateway_input.pack(side="left", padx=2)
        self.gateway_input.insert(0, self.gateway_ip)

        tk.Label(netcfg_frame, text="DNS：", font=("微软雅黑", 9), fg="#555").pack(side="left", padx=(20, 0))
        self.lbl_dns = tk.Label(netcfg_frame, text=self.dns_server,
                                font=("Consolas", 9, "bold"), fg="#1565C0")
        self.lbl_dns.pack(side="left", padx=(2, 20))

        tk.Label(netcfg_frame, text="备用DNS：", font=("微软雅黑", 9), fg="#555").pack(side="left")
        self.lbl_backup_dns = tk.Label(netcfg_frame, text=self.backup_dns,
                                      font=("Consolas", 9, "bold"), fg="#555")
        self.lbl_backup_dns.pack(side="left", padx=(2, 0))

        # 扫描状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.lbl_status = tk.Label(self.root, textvariable=self.status_var,
                                   font=("微软雅黑", 9), fg="#E65100", anchor="w")
        self.lbl_status.pack(fill="x", padx=12, pady=(0, 2))

        tk.Label(self.root, text="扫描日志&在线IP列表", font=("微软雅黑",10)).pack(anchor="w", padx=12)
        self.log_area = scrolledtext.ScrolledText(self.root, font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=10, pady=(0,10))

    def print_log(self, text):
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def on_ip_input_change(self, event=None):
        """当IP输入框内容变化时，自动推导网关第三段"""
        input_text = self.ip_input.get().strip()
        ip_pattern = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})")
        m = ip_pattern.match(input_text)
        if m and 0 <= int(m.group(3)) <= 255:
            seg3 = m.group(3)
            new_gateway = f"172.16.{seg3}.254"
            self.gateway_input.delete(0, tk.END)
            self.gateway_input.insert(0, new_gateway)

    def get_network_config(self):
        """读取当前网络配置"""
        self.subnet_mask = "255.255.255.0"
        self.dns_server = "202.101.172.35"
        self.gateway_ip = self.gateway_input.get().strip() or self.gateway_ip
        self.backup_dns = "8.8.8.8"

    def get_scan_segment(self):
        input_text = self.ip_input.get().strip()
        full_ip_pattern = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
        full_match = full_ip_pattern.match(input_text)
        if full_match:
            seg1, seg2, seg3, seg4 = full_match.groups()
            for seg in [seg1, seg2, seg3, seg4]:
                if not 0 <= int(seg) <= 255:
                    messagebox.showerror("IP格式错误", "IP每段数值必须在0~255之间")
                    return None, None
            return "single", f"{seg1}.{seg2}.{seg3}.{seg4}"

        seg_pattern = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})$")
        seg_match = seg_pattern.match(input_text)
        if seg_match:
            seg1, seg2, seg3 = seg_match.groups()
            for seg in [seg1, seg2, seg3]:
                if not 0 <= int(seg) <= 255:
                    messagebox.showerror("网段格式错误", "网段每段数值必须在0~255之间")
                    return None, None
            return "segment", f"{seg1}.{seg2}.{seg3}"

        messagebox.showerror("输入格式错误",
                             "支持两种输入格式：\n1.固定IP：172.16.4.160（仅检测该IP）\n2.简写网段：172.16.4（扫描整个网段）")
        return None, None

    def ping_ip(self, ip):
        """内网存活检测依旧使用ping，内网ICMP一般不会拦截"""
        cmd = ["ping", "-n", "1", "-w", "200", ip]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    # ==================== 本机网卡枚举 ====================
    def get_local_interfaces(self):
        """
        枚举本机所有活动网卡，返回排序列表（有线优先、无线其次）
        Returns: [{'name': '以太网', 'ip': '172.16.4.7', 'subnet': '172.16.4', 'type': 'wired'}, ...]
        """
        interfaces = []
        try:
            output = subprocess.run(["ipconfig"], capture_output=True, text=True, encoding="gbk").stdout
            current_adapter = None
            for line in output.split("\n"):
                line = line.strip()
                # 匹配网卡名称
                adapter_match = re.match(r"^(.+适配器|^.+adapter)\s*(.+)?:", line, re.IGNORECASE)
                if adapter_match:
                    name = adapter_match.group(0).rstrip(":")
                    current_adapter = name
                    continue
                # 匹配IPv4地址
                ip_match = re.search(r"IPv4.*?:\s*(\d+\.\d+\.\d+\.\d+)", line)
                if ip_match and current_adapter:
                    ip = ip_match.group(1)
                    if ip.startswith("127.") or ip.startswith("169.254"):
                        continue  # 跳过回环和APIPA
                    parts = ip.split(".")
                    subnet = f"{parts[0]}.{parts[1]}.{parts[2]}"
                    # 判断网卡类型
                    name_lower = current_adapter.lower()
                    if "以太网" in name_lower or "ethernet" in name_lower or "pci" in name_lower:
                        atype = "wired"
                    elif "无线" in name_lower or "wlan" in name_lower or "wi-fi" in name_lower or "wireless" in name_lower:
                        atype = "wireless"
                    else:
                        atype = "other"
                    interfaces.append({
                        "name": current_adapter.strip(),
                        "ip": ip,
                        "subnet": subnet,
                        "type": atype,
                    })
        except Exception:
            pass
        # 排序：无线 > 有线 > 其他
        type_order = {"wireless": 0, "wired": 1, "other": 2}
        interfaces.sort(key=lambda x: type_order.get(x["type"], 2))
        return interfaces

    # ==================== 可靠的本地外网自检（不绑定IP） ====================
    def _plain_tcp(self, host, port, timeout=3.0):
        """纯TCP连接测试，不绑定任何源IP，依赖系统路由"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _plain_http(self, host, port, timeout=4):
        """纯HTTP GET测试，验证返回HTTP响应"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.send(f"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
            response = sock.recv(4096).decode(errors="ignore")
            sock.close()
            # 接受任意HTTP响应（包括30x重定向）
            return bool(response and ("HTTP/" in response or "<html" in response.lower()))
        except Exception:
            return False

    def _plain_dns(self, dns_ip="223.5.5.5", timeout=2.5):
        """UDP DNS查询测试，查询多个域名提高可靠性"""
        queries = [
            (b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
             b"\x03www\x05baidu\x03com\x00\x00\x01\x00\x01"),
            (b"\x56\x78\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
             b"\x03www\x05qq\x03com\x00\x00\x01\x00\x01"),
        ]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            for query in queries:
                try:
                    sock.sendto(query, (dns_ip, 53))
                    sock.recvfrom(512)
                    sock.close()
                    return True
                except socket.timeout:
                    continue
            sock.close()
            return False
        except Exception:
            return False

    def _tcp_parallel_probe(self, targets, timeout_per=3.0):
        """并行TCP探测一批目标，返回 (any_ok, ok_count)"""
        ok_count = 0
        with ThreadPoolExecutor(max_workers=min(len(targets), 8)) as executor:
            futures = {}
            for host, port, _ in targets:
                futures[executor.submit(self._plain_tcp, host, port, timeout_per)] = host
            for fut in futures:
                try:
                    if fut.result(timeout=timeout_per + 2):
                        ok_count += 1
                except Exception:
                    pass
        return ok_count > 0, ok_count

    def _self_test_internet(self):
        """
        本机自检：先并行TCP探测全部目标，若全失败则逐个串联重试（避免瞬时网络波动误判）。
        返回 (has_internet: bool, detail: str)
        """
        # ---- 第一轮：并行TCP连公网（最核心） ----
        tcp_ok, tcp_count = self._tcp_parallel_probe(CHECK_TARGETS)

        if not tcp_ok:
            # ---- 第二轮：逐个串联重试（更宽容的超时） ----
            for host, port, _ in CHECK_TARGETS:
                if self._plain_tcp(host, port, timeout=5.0):
                    tcp_ok = True
                    tcp_count = 1
                    break

        if not tcp_ok:
            return False, "TCP全失败 本机无法外连"

        detail = f"TCP ✓({tcp_count}个)"

        # ---- HTTP验证（并行） ----
        http_ok = False
        with ThreadPoolExecutor(max_workers=len(HTTP_CHECK_TARGETS)) as executor:
            futures = {executor.submit(self._plain_http, h, p): h for h, p in HTTP_CHECK_TARGETS}
            for fut in futures:
                try:
                    if fut.result(timeout=6):
                        http_ok = True
                        break
                except Exception:
                    pass
        detail += " | HTTP ✓" if http_ok else " | HTTP ✗"

        # ---- DNS探测（轮询多服务器） ----
        dns_ok = False
        for dns_ip in DNS_SERVERS:
            if self._plain_dns(dns_ip):
                dns_ok = True
                break
        detail += " | DNS ✓" if dns_ok else " | DNS ✗"

        return True, detail

    # ==================== 网卡级外网检测 ====================
    def _test_internet_from_interface(self, local_ip):
        """
        用本机网卡IP绑包测试外网。
        策略：绑包TCP → 纯TCP回退 → 自检兜底。
        不再因单一方法失败而直接判False。
        """
        score = 0
        parts = []

        # ---- TCP绑包探测 ----
        tcp_ok = False
        tcp_cnt = 0
        bind_fail_count = 0
        for host, port, _ in CHECK_TARGETS:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.bind((local_ip, 0))
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    tcp_ok = True
                    tcp_cnt += 1
            except OSError:
                bind_fail_count += 1
            except Exception:
                pass

        if tcp_ok:
            score += 60
            parts.append(f"TCP ✓(绑包 {tcp_cnt})")
        else:
            # 绑包全失败 → 回退纯TCP（不限源IP，依赖系统路由表）
            if bind_fail_count > 0:
                parts.append(f"TCP 绑包失败({bind_fail_count})")
            plain_ok = False
            plain_cnt = 0
            for host, port, _ in CHECK_TARGETS[:6]:  # 仅测前6个高优先级
                if self._plain_tcp(host, port, timeout=3.5):
                    plain_ok = True
                    plain_cnt += 1
            if plain_ok:
                score += 60
                parts.append(f"TCP ✓(回退 {plain_cnt})")
            else:
                # 纯TCP也失败 → 用自检结果兜底
                self_ok = getattr(self, "_self_has_internet", False)
                if self_ok:
                    score += 60
                    parts.append("TCP ✓(自检补正)")
                else:
                    parts.append("TCP ✗")
                    return False, " | ".join(parts)

        # ---- HTTP验证 ----
        http_ok = False
        for host, port in HTTP_CHECK_TARGETS:
            if self._plain_http(host, port):
                http_ok = True
                break
        if http_ok:
            score += 25
            parts.append("HTTP ✓")
        else:
            parts.append("HTTP ✗")

        # ---- DNS探测 ----
        dns_ok = False
        for dns_ip in DNS_SERVERS:
            if self._plain_dns(dns_ip):
                dns_ok = True
                break
        if dns_ok:
            score += 15
            parts.append("DNS ✓")
        else:
            parts.append("DNS ✗")

        return score >= 60, " | ".join(parts) + f" ({score})"

    def _ping_gateway(self, gateway_ip):
        """Ping 网关检测连通性"""
        try:
            cmd = ["ping", "-n", "1", "-w", "300", gateway_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except Exception:
            return False

    def check_ip_has_internet(self, target_ip):
        """
        逐子网独立判定远程IP的外网访问能力。
        判定层级：
        1. 优先：匹配同子网本机网卡 → 用该网卡的外网测试结果
        2. 次优：无匹配网卡 → 检测该子网网关是否通 + 本机自检状态
        3. 兜底：网关不通 → 保守判定为仅内网
        """
        self_ok = getattr(self, "_self_has_internet", False)
        parts = target_ip.split(".")
        target_subnet = f"{parts[0]}.{parts[1]}.{parts[2]}"

        # 推导该子网的网关IP（第三段不变，最后一节.254）
        derived_gateway = f"{target_subnet}.254"

        # ===== 层级1: 查找匹配的本地网卡 =====
        local_interfaces = getattr(self, "_local_interfaces", [])
        for iface in local_interfaces:
            if iface["subnet"] == target_subnet:
                if target_ip == iface["ip"]:
                    has_net = iface.get("has_internet", False)
                    detail = iface.get("internet_detail", "")
                    self._last_detect_detail = f"本机IP[{iface['name']}] {detail}"
                    return has_net
                self._last_detect_detail = (
                    f"同子网目标({target_ip})不使用本机外网判定，仅判定内网"
                )
                return False

        # ===== 层级2: 无匹配网卡，检测网关并依赖自检 =====
        gw_reachable = self._ping_gateway(derived_gateway)

        if gw_reachable and self_ok:
            # 网关通 + 本机能上网 → 推断该子网设备也可上网
            self._last_detect_detail = f"网关{derived_gateway}通 自检补正"
            return True

        if gw_reachable and not self_ok:
            # 网关通但本机不能上网 → 仅内网
            self._last_detect_detail = f"网关{derived_gateway}通 但本机无外网"
            return False

        if not gw_reachable and self_ok:
            # 网关不通但本机能上网 → 可能网关IP不准确，仍用自检结果
            self._last_detect_detail = f"网关{derived_gateway}不通 自检补正"
            return True

        # ===== 层级3: 网关不通且本机无外网 → 保守判定 =====
        self._last_detect_detail = f"网关{derived_gateway}不通 本机无外网"
        return False

    def scan_worker(self):
        while not self.task_queue.empty() and self.is_scanning:
            target_ip = self.task_queue.get()
            try:
                if self.ping_ip(target_ip):
                    has_net = self.check_ip_has_internet(target_ip)
                    detail = getattr(self, '_last_detect_detail', '')
                    if has_net:
                        self.ip_internet_sorted.append(target_ip)
                        self.print_log(f"✅ {target_ip} 在线 | 具备外网 | {detail}")
                    else:
                        self.ip_lan_only_sorted.append(target_ip)
                        self.print_log(f"✅ {target_ip} 在线 | 仅内网 | {detail}")
            except Exception as e:
                self.print_log(f"❌ {target_ip} 检测异常：{str(e)}")
            self.task_queue.task_done()

    def scan_lan(self):
        try:
            scan_mode, scan_value = self.get_scan_segment()
            if scan_mode is None:
                self.is_scanning = False
                self.scan_btn.config(state="normal")
                return
            self.ip_internet_sorted.clear()
            self.ip_lan_only_sorted.clear()
            self.total_online = 0
            self.get_network_config()

            # ===== 第一步：本机外网自检（不绑IP，纯系统路由） =====
            self.print_log(f"========================================")
            self.print_log(f"【本机外网自检】")
            self._self_has_internet, self._self_internet_detail = self._self_test_internet()
            if self._self_has_internet:
                self.print_log(f"  ✅ 本机可访问外网 [{self._self_internet_detail}]")
            else:
                self.print_log(f"  ❌ 本机无法访问外网 [{self._self_internet_detail}]")
                self.print_log(f"  ⚠ 将仅报告设备在线状态，无法判定外网权限")

            # ===== 第二步：枚举本机所有网卡并测试 =====
            self.print_log(f"========================================")
            self.print_log(f"【本机网卡枚举 & 逐网卡外网测试】")
            self._local_interfaces = self.get_local_interfaces()
            if not self._local_interfaces:
                self.print_log(f"  ⚠ 未检测到活动网卡，将使用默认方式检测")
            else:
                for iface in self._local_interfaces:
                    type_tag = "📶无线" if iface["type"] == "wireless" else ("🔌有线" if iface["type"] == "wired" else "🔗其他")
                    self.print_log(f"  [{type_tag}] {iface['name']} → {iface['ip']} ({iface['subnet']}.0/24)")
                    # 用该网卡IP测试外网
                    has_net, detail = self._test_internet_from_interface(iface["ip"])
                    iface["has_internet"] = has_net
                    iface["internet_detail"] = detail
                    status = "✅ 可访问外网" if has_net else "❌ 仅内网"
                    self.print_log(f"         外网检测: {status}  [{detail}]")

            # ===== 第三步：网络配置 & 网关检测 =====
            self.print_log(f"========================================")
            self.print_log(f"【外网检测网络配置】")
            self.print_log(f"  IP 地址：{self.ip_input.get().strip()}")
            self.print_log(f"  子网掩码：{self.subnet_mask}")
            self.print_log(f"  网关地址：{self.gateway_ip}")
            self.print_log(f"  DNS 地址：{self.dns_server}")
            self.print_log(f"  备用 DNS：{self.backup_dns}")

            # 提前检测目标子网网关连通性
            if scan_mode == "single":
                parts = scan_value.split(".")
                target_subnet = f"{parts[0]}.{parts[1]}.{parts[2]}"
            else:
                target_subnet = scan_value
            derived_gw = f"{target_subnet}.254"
            gw_ok = self._ping_gateway(derived_gw)
            self.print_log(f"  目标子网网关 [{derived_gw}]：{'✅ 可达' if gw_ok else '❌ 不可达'}")
            self.print_log(f"========================================")

            # ===== 第四步：开始扫描 =====
            if scan_mode == "single":
                target_ip = scan_value
                self.print_log(f"开始检测固定IP：{target_ip}")
                self.print_log(f"判定层级：网卡匹配→网关检测→自检兜底")
                self.print_log(f"========================================")
                self.task_queue.put(target_ip)
            else:
                segment_prefix = scan_value
                self.print_log(f"开始扫描网段：{segment_prefix}.0 ~ {segment_prefix}.254")
                self.print_log(f"判定层级：网卡匹配→网关检测→自检兜底")
                self.print_log(f"【说明】每个子网独立判定，不跨网段共享结果")
                self.print_log(f"========================================")
                for host_num in range(1, 255):
                    full_ip = f"{segment_prefix}.{host_num}"
                    self.task_queue.put(full_ip)
            worker_list = []
            for _ in range(self.worker_thread_num):
                t = threading.Thread(target=self.scan_worker, daemon=True)
                worker_list.append(t)
                t.start()
            self.task_queue.join()
            self.total_online = len(self.ip_internet_sorted) + len(self.ip_lan_only_sorted)
            self.print_log(f"\n========================================")
            if scan_mode == "single":
                self.print_log(f"固定IP {scan_value} 检测完成")
            else:
                self.print_log(f"网段 {scan_value}.0/24 扫描完成")
            self.print_log(f"在线设备总数：{self.total_online} 台")
            self.print_log(f"具备外网权限设备：{len(self.ip_internet_sorted)} 台")
            self.print_log(f"仅内网互通设备：{len(self.ip_lan_only_sorted)} 台")
            self.print_log(f"========================================\n")
        except Exception as err:
            err_msg = traceback.format_exc()
            self.print_log(f"扫描线程全局异常：\n{err_msg}")
            messagebox.showerror("扫描异常", f"扫描出错：{str(err)}")
        finally:
            self.is_scanning = False
            self.scan_btn.config(state="normal")
            self.root.after(0, self._stop_status_timer)

    def _start_status_timer(self):
        """启动状态计时器"""
        self._scan_start_time = time.time()
        self._update_status()

    def _update_status(self):
        """每秒更新状态栏显示"""
        if not self.is_scanning:
            return
        elapsed = int(time.time() - self._scan_start_time)
        total = 255 if self.task_queue.maxsize > 1 else 1
        done = total - self.task_queue.qsize()
        self.status_var.set(f"⏳ 正在扫描... 已运行 {elapsed}s | 进度 {done}/{total}")
        self._status_timer_id = self.root.after(1000, self._update_status)

    def _stop_status_timer(self):
        """停止计时器并更新最终状态"""
        if hasattr(self, '_status_timer_id'):
            self.root.after_cancel(self._status_timer_id)
        elapsed = int(time.time() - self._scan_start_time) if hasattr(self, '_scan_start_time') else 0
        self.status_var.set(f"✅ 扫描完成 | 总耗时 {elapsed}s | 在线设备 {self.total_online} 台")

    def start_scan_task(self):
        if self.is_scanning:
            messagebox.showinfo("提示", "当前正在扫描，请等待扫描完成！")
            return
        self.is_scanning = True
        self.scan_btn.config(state="disabled")
        self._start_status_timer()
        scan_thread = threading.Thread(target=self.scan_lan, daemon=True)
        scan_thread.start()

    def export_txt_report(self):
        try:
            if self.total_online == 0:
                messagebox.showwarning("提示", "暂无扫描数据，请先执行内网扫描！")
                return
            self.get_network_config()
            with open(self.save_file_path, "w", encoding="utf-8") as f:
                # 本机自检
                self_ok = getattr(self, '_self_has_internet', False)
                self_detail = getattr(self, '_self_internet_detail', '')
                f.write("【本机外网自检结果】\n")
                f.write(f"  {'✅ 可访问外网' if self_ok else '❌ 无法外连'} [{self_detail}]\n")
                f.write("-" * 60 + "\n")
                # 网卡信息
                f.write("【本机网卡信息】\n")
                interfaces = getattr(self, '_local_interfaces', [])
                if interfaces:
                    for iface in interfaces:
                        type_tag = "有线" if iface["type"] == "wired" else ("无线" if iface["type"] == "wireless" else "其他")
                        net_status = "✅ 可访问外网" if iface.get("has_internet") else "❌ 仅内网"
                        detail = iface.get("internet_detail", "")
                        f.write(f"  [{type_tag}] {iface['name']} → {iface['ip']}  {net_status}  [{detail}]\n")
                else:
                    f.write("  (未枚举到网卡)\n")
                f.write("-" * 60 + "\n")
                f.write("【外网检测网络配置】\n")
                f.write(f"  IP 地址：{self.ip_input.get().strip()}\n")
                f.write(f"  子网掩码：{self.subnet_mask}\n")
                f.write(f"  网关地址：{self.gateway_ip}\n")
                f.write(f"  DNS 地址：{self.dns_server}\n")
                f.write(f"  备用 DNS：{self.backup_dns}\n")
                f.write("-" * 60 + "\n")
                f.write("【检测说明】\n")
                f.write("1. 内网存活检测：Ping目标IP（内网ICMP一般不拦截）；\n")
                f.write("2. 外网判定层级：本机IP优先 → 无本机IP时网关检测 → 本机自检兜底；\n")
                f.write("3. 仅当目标IP与本机IP一致时，才使用本机外网测试结果；\n")
                f.write("4. 同子网其他目标设备默认判定为仅内网，避免误判；\n")
                f.write("5. 程序以管理员权限运行，确保Ping和Socket操作正常。\n")
                f.write("-" * 60 + "\n")
                f.write("【仅内网互通设备清单】（TCP外网检测未通过）\n")
                if self.ip_lan_only_sorted:
                    for ip in self.ip_lan_only_sorted:
                        f.write(f"  {ip}\n")
                else:
                    f.write("  (无)\n")
                f.write("\n【具备外网访问权限设备清单】（TCP外网检测通过）\n")
                if self.ip_internet_sorted:
                    for ip in self.ip_internet_sorted:
                        f.write(f"  {ip}\n")
                else:
                    f.write("  (无)\n")
                f.write("\n" + "="*90 + "\n【全局统计汇总信息】\n")
                f.write(f"内网在线设备合计: {self.total_online} 台\n")
                f.write(f"具备外网权限设备: {len(self.ip_internet_sorted)} 台\n")
                f.write(f"仅内网互通设备: {len(self.ip_lan_only_sorted)} 台\n")
                f.write("=" * 90 + "\n")
            messagebox.showinfo("导出成功", f"检测报告已保存至：\n{self.save_file_path}")
        except Exception as e:
            messagebox.showerror("导出失败", f"写入文件异常：{str(e)}")

    def on_window_close(self):
        if self.is_scanning:
            if messagebox.askyesno("确认退出", "当前扫描任务正在运行，确定关闭程序吗？"):
                self.is_scanning = False
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    try:
        elevate_admin()
        main_window = tk.Tk()
        app = NetChecker(main_window)
        main_window.mainloop()
    except Exception as e:
        err_info = traceback.format_exc()
        with open("程序崩溃日志.txt","w",encoding="utf-8") as logf:
            logf.write(err_info)
        import os
        os.system(f"cmd /c echo 程序崩溃，错误信息已保存至【程序崩溃日志.txt】，按任意键关闭窗口 & pause")
