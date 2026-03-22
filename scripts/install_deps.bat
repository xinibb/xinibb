@echo off
REM 欧易量化交易系统 - Windows依赖安装脚本

echo ================================
echo 欧易量化交易系统 - 依赖安装
echo ================================

REM 检查 Python 版本
python --version
echo.

REM 升级 pip
echo 正在升级 pip...
python -m pip install --upgrade pip

REM 安装核心依赖
echo.
echo 正在安装扣子平台依赖...
pip install ^
    cozeloop==0.1.25 ^
    coze-coding-dev-sdk==0.5.11 ^
    coze-coding-utils==0.2.4 ^
    coze-workload-identity==0.1.4

REM 安装 LangGraph 相关依赖
echo.
echo 正在安装 LangGraph 依赖...
pip install ^
    langgraph==1.0.2 ^
    langchain==1.0.3 ^
    langchain-core==1.0.2 ^
    langchain-openai==1.0.1

REM 安装 Web 框架
echo.
echo 正在安装 Web 框架...
pip install ^
    fastapi==0.121.2 ^
    uvicorn==0.34.0 ^
    requests==2.32.3

REM 安装其他依赖
echo.
echo 正在安装其他依赖...
pip install ^
    pydantic==2.12.3 ^
    jinja2==3.1.6 ^
    python-dotenv==1.0.1

REM 验证安装
echo.
echo ================================
echo 验证关键模块...
echo ================================

python -c "import cozeloop; print('✓ cozeloop')"
python -c "import coze_coding_utils; print('✓ coze_coding_utils')"
python -c "import coze_coding_dev_sdk; print('✓ coze_coding_dev_sdk')"
python -c "import coze_workload_identity; print('✓ coze_workload_identity')"
python -c "import langgraph; print('✓ langgraph')"
python -c "import langchain; print('✓ langchain')"
python -c "import fastapi; print('✓ fastapi')"

echo.
echo ================================
echo 安装完成！
echo ================================
echo.
echo 运行命令启动服务:
echo   python src\main.py
echo.
pause
