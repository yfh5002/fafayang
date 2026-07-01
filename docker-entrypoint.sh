#!/bin/sh
set -e

cd /app

# 如果证书不存在，自动生成
if [ ! -f "certs/cert.pem" ] || [ ! -f "certs/key.pem" ]; then
    echo "[Docker] SSL 证书缺失，正在自动生成..."
    mkdir -p certs
    python generate-cert-python.py
    echo "[Docker] 证书生成完成"
fi

# 执行传入的命令（默认是 python main.py）
exec "$@"
