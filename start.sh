#!/bin/bash
# 欧易量化交易系统启动脚本

echo "🚀 欧易量化交易系统"
echo "=================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

# 安装依赖
echo "📦 安装依赖..."
pip3 install -r requirements.txt --quiet

# 创建必要的目录
mkdir -p logs data config

# 启动服务
echo "🎯 启动服务..."
echo ""
echo "访问地址:"
echo "  - 主页: http://localhost:5000"
echo "  - API文档: http://localhost:5000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动FastAPI
python3 backend/api/main.py
