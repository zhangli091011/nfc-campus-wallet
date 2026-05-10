#!/bin/bash
# 重启后端服务脚本

echo "🔄 正在重启NFC钱包后端服务..."
echo "================================"

# 检查是否有服务在运行
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "📍 发现运行中的服务，正在停止..."
    pkill -f "uvicorn.*app.main:app"
    sleep 2
    echo "✅ 服务已停止"
else
    echo "ℹ️  没有发现运行中的服务"
fi

# 启动服务
echo ""
echo "🚀 正在启动服务..."
python start_server.py &

# 等待服务启动
sleep 3

# 检查服务是否启动成功
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "📊 服务信息:"
    echo "   - 地址: http://localhost:8000"
    echo "   - 健康检查: http://localhost:8000/health"
    echo "   - API文档: http://localhost:8000/docs"
    echo ""
    echo "🧪 运行CORS测试:"
    echo "   python test_cors.py"
else
    echo "❌ 服务启动失败，请检查日志"
    exit 1
fi
