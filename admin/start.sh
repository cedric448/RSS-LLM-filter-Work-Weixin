#!/bin/bash
# RSS 源管理后台启动脚本

echo "=========================================="
echo "🚀 RSS 源管理后台"
echo "=========================================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚠️  警告: .env 文件不存在，使用默认配置"
    echo "💡 提示: 复制 .env.example 为 .env 并修改授权码"
fi

# 安装依赖
echo "📦 安装依赖..."
pip3 install -q -r requirements.txt

# 显示授权码信息（仅显示前后各5个字符，中间用*号代替）
if [ -f .env ]; then
    AUTH_CODE=$(grep RSS_ADMIN_AUTH_CODE .env | cut -d '=' -f2)
    if [ -n "$AUTH_CODE" ]; then
        AUTH_CODE_DISPLAY="${AUTH_CODE:0:5}...${AUTH_CODE: -5}"
        echo "🔐 授权码: $AUTH_CODE_DISPLAY"
    fi
fi

# 启动应用
echo "🌐 启动后台服务..."
echo ""
echo "访问地址: http://localhost:5002"
echo "授权码: 请查看 .env 文件中的 RSS_ADMIN_AUTH_CODE"
echo "按 Ctrl+C 停止服务"
echo ""

python3 app.py
