#!/bin/bash

# 欧易量化交易系统 - 依赖安装脚本
# 系统要求：Linux/Mac

echo "================================"
echo "欧易量化交易系统 - 依赖安装"
echo "系统要求：Linux/Mac"
echo "================================"

# 检查 Python 版本
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python 版本: $PYTHON_VERSION"

# 升级 pip
echo ""
echo "正在升级 pip..."
python -m pip install --upgrade pip -q

# 安装核心依赖
echo ""
echo "正在安装扣子平台依赖..."
pip install -q \
    cozeloop==0.1.25 \
    coze-coding-dev-sdk==0.5.11 \
    coze-coding-utils==0.2.4 \
    coze-workload-identity==0.1.4

# 安装 LangGraph 相关依赖
echo ""
echo "正在安装 LangGraph 依赖..."
pip install -q \
    langgraph==1.0.2 \
    langchain==1.0.3 \
    langchain-core==1.0.2 \
    langchain-openai==1.0.1

# 安装 Web 框架
echo ""
echo "正在安装 Web 框架..."
pip install -q \
    fastapi==0.121.2 \
    uvicorn==0.34.0 \
    requests==2.32.3

# 安装其他依赖
echo ""
echo "正在安装其他依赖..."
pip install -q \
    pydantic==2.12.3 \
    jinja2==3.1.6 \
    python-dotenv==1.0.1

# 验证安装
echo ""
echo "================================"
echo "验证关键模块..."
echo "================================"

python -c "
import sys
modules = [
    'cozeloop',
    'coze_coding_utils',
    'coze_coding_dev_sdk',
    'coze_workload_identity',
    'langgraph',
    'langchain',
    'fastapi',
    'uvicorn',
]

failed = []
for module in modules:
    try:
        __import__(module)
        print(f'✓ {module}')
    except ImportError as e:
        print(f'✗ {module}: {e}')
        failed.append(module)

if failed:
    print(f'\n❌ 以下模块安装失败: {\", \".join(failed)}')
    sys.exit(1)
else:
    print('\n✅ 所有核心模块安装成功！')
"

echo ""
echo "================================"
echo "安装完成！"
echo "================================"
echo ""
echo "运行命令启动服务:"
echo "  python src/main.py"
echo ""
