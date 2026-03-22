#!/bin/bash

# 欧易量化交易系统 - 一键启动脚本

echo "================================"
echo "欧易量化交易系统 - 一键启动"
echo "================================"
echo ""

# 检查依赖
echo "🔍 检查依赖..."
python -c "import cozeloop" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少依赖，正在安装..."
    ./scripts/install_deps.sh
fi

echo "✅ 依赖检查通过"
echo ""

# 询问运行模式
echo "请选择运行模式:"
echo "  1) 测试模式（验证系统是否正常）"
echo "  2) 启动服务（HTTP API服务）"
echo "  3) 退出"
echo ""
read -p "请输入选项 [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动测试模式..."
        python scripts/test_workflow.py
        ;;
    2)
        echo ""
        echo "🚀 启动HTTP服务..."
        echo "服务地址: http://localhost:5000"
        echo "按 Ctrl+C 停止服务"
        echo ""
        python src/main.py
        ;;
    3)
        echo "退出"
        exit 0
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac
