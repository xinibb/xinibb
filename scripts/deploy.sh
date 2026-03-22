#!/bin/bash

# 欧易量化交易系统 - 完整部署脚本
# 支持：依赖安装、环境检查、服务启动、测试验证

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/logs/deploy.log"

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

# 显示横幅
show_banner() {
    echo ""
    echo "========================================"
    echo "  欧易量化交易系统 - 自动部署"
    echo "========================================"
    echo ""
}

# 检查系统要求
check_system() {
    log "检查系统要求..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        log_error "不支持 Windows 系统"
        exit 1
    fi
    
    log_info "操作系统: $OSTYPE ✓"
    
    # 检查 Python 版本
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
        log_error "Python 版本过低: $PYTHON_VERSION (需要 >= 3.10)"
        exit 1
    fi
    
    log_info "Python 版本: $PYTHON_VERSION ✓"
    
    # 检查 pip
    if ! command -v pip &> /dev/null; then
        log_error "未找到 pip，请先安装 pip"
        exit 1
    fi
    
    log_info "pip 已安装 ✓"
}

# 创建虚拟环境
create_venv() {
    log "创建虚拟环境..."
    
    if [ -d "$PROJECT_ROOT/venv" ]; then
        log_warning "虚拟环境已存在"
        read -p "是否删除并重新创建？ (y/n): " choice
        if [[ $choice == "y" ]] || [[ $choice == "Y" ]]; then
            rm -rf "$PROJECT_ROOT/venv"
            log_info "已删除旧的虚拟环境"
        else
            log_info "使用现有虚拟环境"
            return
        fi
    fi
    
    python -m venv "$PROJECT_ROOT/venv"
    log "虚拟环境创建成功 ✓"
}

# 激活虚拟环境
activate_venv() {
    log "激活虚拟环境..."
    
    if [ ! -d "$PROJECT_ROOT/venv" ]; then
        log_error "虚拟环境不存在"
        exit 1
    fi
    
    source "$PROJECT_ROOT/venv/bin/activate"
    log "虚拟环境已激活 ✓"
}

# 安装依赖
install_dependencies() {
    log "安装依赖包..."
    
    # 升级 pip
    log_info "升级 pip..."
    pip install --upgrade pip -q
    
    # 安装核心依赖
    log_info "安装核心依赖..."
    pip install -q \
        cozeloop==0.1.25 \
        coze-coding-dev-sdk==0.5.11 \
        coze-coding-utils==0.2.4 \
        coze-workload-identity==0.1.4
    
    # 安装 LangGraph
    log_info "安装 LangGraph..."
    pip install -q \
        langgraph==1.0.2 \
        langchain==1.0.3 \
        langchain-core==1.0.2
    
    # 安装 Web 框架
    log_info "安装 Web 框架..."
    pip install -q \
        fastapi==0.121.2 \
        uvicorn==0.38.0 \
        requests==2.32.5
    
    # 安装其他依赖
    log_info "安装其他依赖..."
    pip install -q \
        pydantic==2.12.3 \
        jinja2==3.1.6 \
        python-dotenv==1.2.1 \
        loguru==0.7.3
    
    log "所有依赖安装完成 ✓"
}

# 验证安装
verify_installation() {
    log "验证安装..."
    
    FAILED=0
    
    # 检查核心模块
    MODULES=(
        "cozeloop"
        "coze_coding_utils"
        "coze_coding_dev_sdk"
        "coze_workload_identity"
        "langgraph"
        "langchain"
        "fastapi"
        "uvicorn"
        "requests"
        "pydantic"
    )
    
    for module in "${MODULES[@]}"; do
        if python -c "import $module" 2>/dev/null; then
            log_info "✓ $module"
        else
            log_error "✗ $module - 导入失败"
            FAILED=1
        fi
    done
    
    if [ $FAILED -eq 1 ]; then
        log_error "部分模块安装失败，请检查日志"
        return 1
    fi
    
    log "所有模块验证通过 ✓"
    return 0
}

# 运行测试
run_tests() {
    log "运行测试..."
    
    if [ -f "$PROJECT_ROOT/scripts/test_workflow.py" ]; then
        python "$PROJECT_ROOT/scripts/test_workflow.py"
        if [ $? -eq 0 ]; then
            log "测试通过 ✓"
            return 0
        else
            log_error "测试失败"
            return 1
        fi
    else
        log_warning "测试脚本不存在，跳过"
        return 0
    fi
}

# 启动服务
start_service() {
    log "启动服务..."
    
    # 检查端口是否被占用
    PORT=5000
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "端口 $PORT 已被占用"
        read -p "是否停止现有服务并重启？ (y/n): " choice
        if [[ $choice == "y" ]] || [[ $choice == "Y" ]]; then
            lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
            log_info "已停止现有服务"
        else
            log_info "使用其他端口"
            PORT=8080
        fi
    fi
    
    log "服务启动中..."
    log "访问地址: http://localhost:$PORT"
    log "按 Ctrl+C 停止服务"
    echo ""
    
    cd "$PROJECT_ROOT"
    python src/main.py --port $PORT
}

# 完整部署流程
full_deploy() {
    show_banner
    
    log "开始完整部署流程..."
    echo ""
    
    # 1. 检查系统
    check_system
    echo ""
    
    # 2. 创建虚拟环境
    create_venv
    echo ""
    
    # 3. 激活虚拟环境
    activate_venv
    echo ""
    
    # 4. 安装依赖
    install_dependencies
    echo ""
    
    # 5. 验证安装
    if ! verify_installation; then
        log_error "安装验证失败"
        exit 1
    fi
    echo ""
    
    # 6. 运行测试
    if ! run_tests; then
        log_warning "测试未通过，但可以继续启动服务"
    fi
    echo ""
    
    # 7. 启动服务
    start_service
}

# 主菜单
main() {
    show_banner
    
    echo "请选择操作:"
    echo "  1) 完整部署（推荐）"
    echo "  2) 仅安装依赖"
    echo "  3) 仅启动服务"
    echo "  4) 运行测试"
    echo "  5) 检查系统要求"
    echo "  6) 退出"
    echo ""
    read -p "请输入选项 [1-6]: " choice
    
    case $choice in
        1)
            full_deploy
            ;;
        2)
            check_system
            create_venv
            activate_venv
            install_dependencies
            verify_installation
            ;;
        3)
            activate_venv
            start_service
            ;;
        4)
            activate_venv
            run_tests
            ;;
        5)
            check_system
            ;;
        6)
            log "退出"
            exit 0
            ;;
        *)
            log_error "无效选项"
            exit 1
            ;;
    esac
}

# 执行主函数
main
