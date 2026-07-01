# -*- coding: utf-8 -*-
"""
HJSYSTEM 证书验证工具
替代 verify_cert.js - 查看服务器证书信息
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
CERT_FILE = BASE_DIR / "certs" / "cert.pem"
CA_FILE = BASE_DIR / "certs" / "ca.crt"

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("错误：需要安装 cryptography 库")
    print("请运行：pip install cryptography")
    sys.exit(1)


def print_cert_info(label, cert_path):
    """打印证书信息"""
    if not cert_path.exists():
        print(f"[{label}] 文件不存在: {cert_path}")
        return

    with open(cert_path, "rb") as f:
        pem_data = f.read()

    cert = x509.load_pem_x509_certificate(pem_data, default_backend())

    print(f"[{label}] 证书路径: {cert_path}")
    print(f"  Subject:     {cert.subject.rfc4514_string()}")
    print(f"  Issuer:      {cert.issuer.rfc4514_string()}")

    # 有效期
    not_before = cert.not_valid_before_utc
    not_after = cert.not_valid_after_utc
    print(f"  Valid From:  {not_before}")
    print(f"  Valid To:    {not_after}")

    # 序列号
    print(f"  Serial:      {hex(cert.serial_number)}")

    # SHA1 指纹
    fingerprint = cert.fingerprint(hashes.SHA1())
    thumb = ":".join(f"{b:02X}" for b in fingerprint)
    print(f"  Thumbprint:  {thumb}")

    # SAN (主题备用名称)
    try:
        san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        san = san_ext.value
        dns_names = san.get_values_for_type(x509.DNSName)
        ip_addrs = san.get_values_for_type(x509.IPAddress)
        print(f"  SAN DNS:     {', '.join(dns_names) if dns_names else '(none)'}")
        print(f"  SAN IP:      {', '.join(str(ip) for ip in ip_addrs) if ip_addrs else '(none)'}")
    except x509.ExtensionNotFound:
        print("  SAN:         (none)")

    print()


def main():
    print("=" * 50)
    print("  HJSYSTEM 证书验证工具")
    print("=" * 50)
    print()

    print_cert_info("服务器证书", CERT_FILE)
    print_cert_info("CA 根证书", CA_FILE)

    # 验证证书链
    if CERT_FILE.exists() and CA_FILE.exists():
        print("-" * 50)
        print("  证书链验证")
        print("-" * 50)
        try:
            with open(CERT_FILE, "rb") as f:
                server_pem = f.read()
            with open(CA_FILE, "rb") as f:
                ca_pem = f.read()

            server_cert = x509.load_pem_x509_certificate(server_pem, default_backend())
            ca_cert = x509.load_pem_x509_certificate(ca_pem, default_backend())

            ca_public_key = ca_cert.public_key()
            ca_public_key.verify(
                server_cert.signature,
                server_cert.tbs_certificate_bytes,
                server_cert.signature_algorithm_parameters,
            )
            print("[OK] 服务器证书由 CA 签发，验证通过")

            # 检查有效期
            now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            if now < server_cert.not_valid_before_utc:
                print("[错误] 服务器证书尚未生效！")
            elif now > server_cert.not_valid_after_utc:
                print("[错误] 服务器证书已过期！")
            else:
                print("[OK] 服务器证书在有效期内")
        except Exception as e:
            print(f"[错误] 证书链验证失败: {e}")

    print()
    print("注意: 以上信息未验证证书是否被撤销（CRL/OCSP）")
    print()
    input("按 Enter 键退出...")


if __name__ == "__main__":
    main()
