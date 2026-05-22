#!/bin/bash
set -e

echo "=== DayAgent Deploy ==="
echo ""

# 检查 .env 是否存在
if [ ! -f ".env" ]; then
    echo "[错误] .env 文件不存在！"
    echo "请先执行: cp .env.example .env && vim .env"
    exit 1
fi

# 检查 .env 权限
if [ "$(stat -c %a .env)" != "600" ]; then
    echo "[警告] .env 权限不是 600，正在修复..."
    chmod 600 .env
fi

echo "[1/3] git pull..."
git pull

echo "[2/3] docker compose build..."
docker compose build

echo "[3/3] docker compose up -d..."
docker compose up -d

echo ""
echo "=== 容器状态 ==="
docker compose ps

echo ""
echo "=== 部署完成 ==="
echo "检查日志: docker compose logs -f"
