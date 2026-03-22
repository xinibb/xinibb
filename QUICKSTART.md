# 欧易量化交易系统 - 快速开始指南

> **⚠️ 系统要求**: 本系统仅支持 Linux/Mac 环境，不支持 Windows

## 🚀 快速安装

### 方法一：使用安装脚本（推荐）

```bash
# 添加执行权限
chmod +x scripts/install_deps.sh

# 运行安装脚本
./scripts/install_deps.sh
```

### 方法二：手动安装

```bash
# 1. 升级 pip
python -m pip install --upgrade pip

# 2. 安装扣子平台依赖
pip install \
    cozeloop==0.1.25 \
    coze-coding-dev-sdk==0.5.11 \
    coze-coding-utils==0.2.4 \
    coze-workload-identity==0.1.4

# 3. 安装 LangGraph 依赖
pip install \
    langgraph==1.0.2 \
    langchain==1.0.3 \
    langchain-core==1.0.2

# 4. 安装 Web 框架
pip install fastapi uvicorn requests

# 5. 安装其他依赖
pip install pydantic jinja2 python-dotenv
```

### 方法三：从 requirements.txt 安装

```bash
pip install -r requirements.txt
```

## ✅ 验证安装

运行以下命令验证所有关键模块是否安装成功：

```bash
python -c "
import cozeloop
import coze_coding_utils
import coze_coding_dev_sdk
import coze_workload_identity
import langgraph
import langchain
import fastapi
print('✅ 所有模块安装成功！')
"
```

## 🏃 启动服务

安装完成后，运行以下命令启动服务：

```bash
python src/main.py
```

服务将在 `http://localhost:5000` 启动。

## 🔧 常见问题

### 1. ModuleNotFoundError: No module named 'cozeloop'

**解决方案:**
```bash
pip install cozeloop==0.1.25
```

### 2. Python 版本不兼容

**要求:** Python 3.10 或更高版本

**检查版本:**
```bash
python --version
```

### 3. 权限问题

**使用虚拟环境（推荐）:**
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 4. 网络问题导致安装失败

**使用国内镜像:**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 📦 核心依赖列表

| 包名 | 版本 | 用途 |
|------|------|------|
| cozeloop | 0.1.25 | 扣子平台核心库 |
| coze-coding-dev-sdk | 0.5.11 | 大语言模型SDK |
| coze-coding-utils | 0.2.4 | 扣子工具库 |
| coze-workload-identity | 0.1.4 | 身份认证 |
| langgraph | 1.0.2 | 工作流编排框架 |
| langchain | 1.0.3 | LLM应用框架 |
| fastapi | 0.121.2 | Web框架 |
| uvicorn | 0.34.0 | ASGI服务器 |
| pydantic | 2.12.3 | 数据验证 |
| requests | 2.32.3 | HTTP客户端 |

## 🎯 下一步

安装完成后，您可以：

1. **启动服务**: `python src/main.py`
2. **查看文档**: 阅读 `AGENTS.md` 了解系统架构
3. **配置参数**: 修改 `config/` 目录下的配置文件
4. **开始交易**: 调用API启动量化交易

## 💡 提示

- ✅ 仅支持 Linux/Mac 环境
- ✅ 建议使用虚拟环境隔离项目依赖
- ✅ 首次运行前请确保所有依赖都已安装
- ✅ 如遇到问题，请检查 Python 版本和依赖版本是否匹配
