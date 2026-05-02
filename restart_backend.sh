#!/bin/bash

# 重启 NFC 钱包后端服务脚本

echo "正在停止后端服务..."
pkill -f "uvicorn app.main:app" || pkill -f "python.*start_server.py"

echo "等待进程完全停止..."
sleep 2

echo "正在启动后端服务..."
cd /home/ubuntu/nfc-campus-wallet

# 激活虚拟环境并启动服务
source .venv/bin/activate
nohup python start_server.py > backend.log 2>&1 &

echo "后端服务已启动，PID: $!"
echo "查看日志: tail -f backend.log"
echo ""
echo "等待服务启动..."
sleep 3

# 检查服务是否正常运行
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ 后端服务启动成功！"
    echo "API 文档: http://localhost:8000/docs"
else
    echo "❌ 后端服务启动失败，请检查日志"
    tail -20 backend.log
fi
