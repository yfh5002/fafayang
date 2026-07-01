# -*- coding: utf-8 -*-
"""
HJSYSTEM SSL Certificate Generator
使用 Python 生成 SSL 证书（替代 Node.js 版本）
"""

import sys
import datetime
import ipaddress
from pathlib import Path

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("错误：需要安装 cryptography 库")
    print("请运行：pip install cryptography")
    sys.exit(1)

from backend.utils import CERT_DIR, get_local_ips

cert_dir = CERT_DIR
cert_dir.mkdir(exist_ok=True)

print("=" * 50)
print("   HJSYSTEM 证书生成 (Python 版本)")
print("=" * 50)
print()

# ========== 生成 CA ==========
print("[1/5] 生成 CA 私钥...")
ca_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

print("[2/5] 生成 CA 证书...")
ca_subject = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HJSYSTEM"),
    x509.NameAttribute(NameOID.COMMON_NAME, "HJSYSTEM CA"),
])

ca_cert = x509.CertificateBuilder().subject_name(
    ca_subject
).issuer_name(
    ca_subject
).public_key(
    ca_key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.now(datetime.timezone.utc)
).not_valid_after(
    datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)
).add_extension(
    x509.BasicConstraints(ca=True, path_length=None),
    critical=True,
).sign(ca_key, hashes.SHA256(), default_backend())

# ========== 生成服务器证书 ==========
print("[3/5] 生成服务器私钥...")
server_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# 收集所有 IP（包含 127.0.0.1 + 实际局域网 IP）
all_ips = ["127.0.0.1"] + get_local_ips()
print(f"[4/5] 检测到以下 IP 地址:")
for ip in all_ips:
    print(f"   - {ip}")

print("[5/5] 生成服务器证书...")
server_subject = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HJSYSTEM"),
    x509.NameAttribute(NameOID.COMMON_NAME, "HJSYSTEM Server"),
])

# 构建 SAN：localhost + 所有 IP + 常见局域网 IP 段（确保其他电脑访问时证书有效）
san_list = [
    x509.DNSName("localhost"),
    x509.DNSName("*"),  # 通配符，匹配任意域名
]
# 添加本机所有 IP
for ip in all_ips:
    try:
        ip_addr = ipaddress.ip_address(ip)
        san_list.append(x509.IPAddress(ip_addr))
        print("   [OK] 添加 IP: " + ip)
    except Exception as e:
        print("   [SKIP] 跳过 IP " + ip + ": " + str(e))

# 添加常见局域网 IP 段（确保其他电脑通过 IP 访问时证书有效）
common_lan_ips = []
for i in range(1, 255):
    for prefix in ["192.168", "10", "172.16", "172.17", "172.18", "172.19", "172.20", "172.21", "172.22", "172.23", "172.24", "172.25", "172.26", "172.27", "172.28", "172.29", "172.30", "172.31"]:
        if "." in prefix:
            common_lan_ips.append(f"{prefix}.{i}")
        else:
            for j in range(1, 255):
                common_lan_ips.append(f"{prefix}.{i}.{j}")

# 限制数量避免证书过大，只添加当前网段相关的 IP
# 实际方案：添加当前 IP 所在网段的所有 IP
for detected_ip in all_ips:
    if detected_ip.count(".") == 3:
        parts = detected_ip.split(".")
        # 添加 /24 网段的所有 IP
        for i in range(1, 255):
            try:
                ip_addr = ipaddress.ip_address(f"{parts[0]}.{parts[1]}.{parts[2]}.{i}")
                if x509.IPAddress(ip_addr) not in san_list:
                    san_list.append(x509.IPAddress(ip_addr))
            except Exception:
                pass
        print(f"   [OK] 添加网段 {parts[0]}.{parts[1]}.{parts[2]}.*")

server_cert = x509.CertificateBuilder().subject_name(
    server_subject
).issuer_name(
    ca_subject
).public_key(
    server_key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.now(datetime.timezone.utc)
).not_valid_after(
    datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650)
).add_extension(
    x509.SubjectAlternativeName(san_list),
    critical=False,
).sign(ca_key, hashes.SHA256(), default_backend())

# ========== 保存文件 ==========
print()
print("正在保存证书文件...")

files = [
    (cert_dir / "ca.key", ca_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption())),
    (cert_dir / "ca.crt", ca_cert.public_bytes(serialization.Encoding.PEM)),
    (cert_dir / "key.pem", server_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption())),
    (cert_dir / "cert.pem", server_cert.public_bytes(serialization.Encoding.PEM)),
]

for path, data in files:
    path.write_bytes(data)
    print(f"  [OK] {path.name}")

print()
print("=" * 50)
print("[OK] 证书生成成功！")
print("=" * 50)
print()
print("证书位置:")
for path, _ in files:
    print(f"  - {path}")
print()
print("下一步:")
print("1. 以管理员身份运行：python install_cert.py")
print("2. 安装 CA 证书到系统信任库")
print("3. 重启浏览器访问：https://localhost:5002")
print()
