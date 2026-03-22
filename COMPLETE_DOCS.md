# 欧易量化交易系统 - 完整文档

> **⚠️ 系统要求**: 本系统仅支持 Linux/Mac 环境，不支持 Windows

---

## 📋 目录

1. [项目概述](#项目概述)
2. [快速开始](#快速开始)
3. [详细安装](#详细安装)
4. [本地使用指南](#本地使用指南)
5. [API文档](#api文档)
6. [前端页面](#前端页面)
7. [成本优化](#成本优化)
8. [配置说明](#配置说明)
9. [常见问题](#常见问题)

---

## 项目概述

- **名称**: 欧易量化交易系统（OKX Quantitative Trading System）
- **功能**: 基于剥头皮策略的自动化量化交易工作流
- **特性**:
  - ✅ 实时行情监控（欧易API）
  - ✅ 剥头皮策略分析（大语言模型驱动）
  - ✅ 自动化交易执行
  - ✅ 风险管理（止损/止盈/仓位控制）
  - ✅ 多渠道通知推送（邮件）
  - ✅ Web界面实时监控

---

## 快速开始

### 一键启动（推荐）

```bash
# 1. 安装依赖
chmod +x scripts/install_deps.sh
./scripts/install_deps.sh

# 2. 启动服务（包含Web界面）
python src/main.py

# 3. 访问Web界面
# 浏览器打开 http://localhost:5000
```

### 手动启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python src/main.py
```

---

## 详细安装

### 系统要求

- **操作系统**: Linux / macOS
- **Python**: 3.10 或更高版本
- **内存**: 建议 4GB 以上
- **网络**: 稳定的互联网连接

### 检查Python版本

```bash
python --version
# 或
python3 --version
```

### 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac

# 验证激活
which python  # 应显示 venv/bin/python
```

### 安装依赖

#### 方法一：自动安装（推荐）

```bash
chmod +x scripts/install_deps.sh
./scripts/install_deps.sh
```

#### 方法二：手动安装

```bash
# 升级 pip
pip install --upgrade pip

# 安装扣子平台依赖
pip install \
    cozeloop==0.1.25 \
    coze-coding-dev-sdk==0.5.11 \
    coze-coding-utils==0.2.4 \
    coze-workload-identity==0.1.4

# 安装 LangGraph 依赖
pip install \
    langgraph==1.0.2 \
    langchain==1.0.3 \
    langchain-core==1.0.2

# 安装 Web 框架
pip install fastapi uvicorn requests

# 安装其他依赖
pip install pydantic jinja2 python-dotenv

# 或从 requirements.txt 安装
pip install -r requirements.txt
```

### 验证安装

```bash
python -c "
import cozeloop
import coze_coding_utils
import coze_coding_dev_sdk
import coze_workload_identity
import langgraph
import langchain
import fastapi
print('✅ 所有核心依赖安装成功！')
"
```

---

## 本地使用指南

### 环境准备

#### 系统要求
- **操作系统**: Linux / macOS（不支持 Windows）
- **Python**: 3.10 或更高版本
- **内存**: 建议 4GB 以上
- **网络**: 稳定的互联网连接

### 快速测试

#### 运行测试脚本

```bash
python scripts/test_workflow.py
```

**预期输出：**
```
============================================================
欧易量化交易系统 - 功能测试
============================================================

📊 测试参数:
  交易对: BTC-USDT
  初始资金: $10000.0
  策略类型: scalping
  风控配置: 止损2.0% / 止盈5.0%

🚀 开始执行工作流...
------------------------------------------------------------

✅ 工作流执行成功！
------------------------------------------------------------

📈 执行结果:
  状态: success
  消息: 交易监控完成
  总收益: $0.00
  收益率: 0.00%
  风险等级: low
  最后交易时间: 2026-03-22 xx:xx:xx

============================================================
✅ 测试完成！系统运行正常
============================================================
```

### 启动服务

#### 方式一：直接启动（开发模式）

```bash
python src/main.py
```

**输出：**
```
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### 方式二：指定端口启动

```bash
python src/main.py --port 8080
```

#### 方式三：后台运行

```bash
# 启动
nohup python src/main.py > logs/server.log 2>&1 &

# 查看日志
tail -f logs/server.log

# 停止服务
ps aux | grep "python src/main.py" | awk '{print $2}' | xargs kill
```

---

## API文档

服务启动后，可以通过 HTTP API 调用工作流。

### API 端点

- **服务地址**: `http://localhost:5000`
- **主要接口**: `/invoke` - 执行工作流

### 示例 1: 基础调用（使用 curl）

```bash
curl -X POST http://localhost:5000/invoke \
  -H "Content-Type: application/json" \
  -d '{"trading_pair":"BTC-USDT"}'
```

### 示例 2: 完整参数调用

```bash
curl -X POST http://localhost:5000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "trading_pair": "BTC-USDT",
    "initial_capital": 10000.0,
    "strategy_type": "scalping",
    "risk_config": {
      "max_position_ratio": 0.3,
      "stop_loss_percent": 0.02,
      "take_profit_percent": 0.05
    },
    "notification_config": {
      "enable_email": true,
      "email_recipients": ["user@example.com"]
    }
  }'
```

### 示例 3: Python 调用

```python
import requests

# 基础调用
response = requests.post(
    "http://localhost:5000/invoke",
    json={
        "trading_pair": "BTC-USDT",
        "initial_capital": 10000.0
    }
)

print(response.json())

# 完整参数调用
response = requests.post(
    "http://localhost:5000/invoke",
    json={
        "trading_pair": "BTC-USDT",
        "initial_capital": 10000.0,
        "strategy_type": "scalping",
        "risk_config": {
            "max_position_ratio": 0.3,
            "stop_loss_percent": 0.02,
            "take_profit_percent": 0.05
        }
    }
)

result = response.json()
print(f"状态: {result['status']}")
print(f"消息: {result['message']}")
print(f"风险等级: {result['risk_level']}")
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `trading_pair` | string | 是 | - | 交易对，如 "BTC-USDT" |
| `initial_capital` | float | 否 | 10000.0 | 初始资金（美元） |
| `strategy_type` | string | 否 | "scalping" | 策略类型 |
| `risk_config.max_position_ratio` | float | 否 | 0.3 | 最大仓位比例 |
| `risk_config.stop_loss_percent` | float | 否 | 0.02 | 止损百分比 |
| `risk_config.take_profit_percent` | float | 否 | 0.05 | 止盈百分比 |

### 返回值说明

```json
{
  "status": "success",           // 执行状态
  "message": "交易监控完成",      // 消息
  "total_profit": 0.0,           // 总收益
  "profit_rate": 0.0,            // 收益率
  "trade_count": 0,              // 交易次数
  "last_trade_time": "2026-03-22 15:04:31",  // 最后交易时间
  "risk_level": "low"            // 风险等级
}
```

---

## 前端页面

### 功能特性

Web界面提供以下功能：

1. **实时行情监控**
   - 当前价格显示
   - 24小时价格变化
   - 成交量统计
   - 市场趋势分析

2. **账户资产管理**
   - 账户余额查看
   - 可用余额显示
   - 持仓价值统计
   - 收益率计算

3. **交易信号展示**
   - 买卖信号指示
   - 信号强度评估
   - 建议价格和数量
   - 决策理由说明

4. **风险监控**
   - 风险等级评估
   - 止损止盈状态
   - 仓位比例监控
   - 异常告警提示

5. **执行日志**
   - 实时日志显示
   - 历史操作记录
   - 错误信息提示
   - 性能指标统计

### 访问方式

浏览器打开：http://localhost:5000

### 界面截图

```
┌─────────────────────────────────────────────────────┐
│  欧易量化交易监控系统             [运行中] [刷新]    │
├─────────────────────────────────────────────────────┤
│  交易对: [BTC-USDT ▼]  [执行策略]                   │
├─────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  │ 当前价格 │  │ 账户余额 │  │ 持仓价值 │  │ 总收益   │
│  │ $43,250  │  │ $10,000  │  │ $3,000   │  │ +$150    │
│  │ +2.5% ↑  │  │ 可用$7K  │  │ 30%仓位  │  │ 1.5%     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘
├─────────────────────────────────────────────────────┤
│  市场行情                                           │
│  趋势: 上涨  成交量: 125M  最高: $44,000  最低: $42,500│
├─────────────────────────────────────────────────────┤
│  交易信号                                           │
│  ┌─────────┐  信号强度: 75%                         │
│  │  买入   │  建议价格: $43,255                     │
│  │  BUY    │  建议数量: 0.023 BTC                   │
│  └─────────┘  理由: 突破阻力位，成交量放大          │
├─────────────────────────────────────────────────────┤
│  风险监控                                           │
│  风险等级: 低风险  止损: 正常  止盈: 未达到  仓位: 30%│
└─────────────────────────────────────────────────────┘
```

---

## 成本优化

### 📊 积分消耗分析

#### ✅ 会消耗积分的功能

| 功能 | 节点 | 消耗情况 | 频率 |
|------|------|---------|------|
| **策略决策** | `strategy_decision_node` | **~0.005积分/次** | 每次监控循环 |
| 大语言模型调用 | LLMClient.invoke() | 取决于模型和token | 高频 |

#### ❌ 不会消耗积分的功能

| 功能 | 节点 | 说明 |
|------|------|------|
| 行情监控 | `market_monitor_node` | 欧易公开API，免费 |
| 资产管理 | `asset_manage_node` | 模拟数据，免费 |
| 风险管理 | `risk_manage_node` | 本地计算，免费 |
| 交易执行 | `trade_execute_node` | 欧易API，免费 |
| 邮件通知 | `notification_node` | SMTP协议，免费 |
| 工作流编排 | LangGraph | 本地运行，免费 |

### 💸 成本估算

#### 场景1：持续监控（24小时）
- 监控频率：每分钟1次
- 每小时调用：60次策略决策
- 每小时消耗：~0.3积分
- **每天消耗：~7.2积分**
- **每月消耗：~216积分**

#### 场景2：间歇监控（8小时/天）
- 每天消耗：~2.4积分
- **每月消耗：~72积分**

#### 场景3：低频监控（每5分钟1次）
- 每小时调用：12次策略决策
- **每天消耗：~1.44积分**
- **每月消耗：~43积分**

### 🎯 降低成本的方案

#### 方案1：使用本地大模型（推荐，完全免费）

修改代码使用本地部署的开源大模型，如：
- **Ollama** (Llama 3, Qwen等)
- **LM Studio**
- **vLLM**

**优点**:
- ✅ 完全免费
- ✅ 无网络延迟
- ✅ 数据隐私安全

**缺点**:
- ❌ 需要本地GPU资源
- ❌ 模型能力略弱于云端

#### 方案2：降低监控频率

修改监控间隔从1分钟改为5-10分钟：

```python
# 在 loop_graph.py 中添加延迟
import time
time.sleep(300)  # 5分钟间隔
```

**节省**: 可降低 **80-90%** 积分消耗

#### 方案3：使用更便宜的模型

修改配置使用更经济的模型：

```json
{
  "config": {
    "model": "doubao-seed-1-6-lite-251015",  // 更便宜的模型
    "temperature": 0.3,
    "max_completion_tokens": 1000  // 减少输出token
  }
}
```

**节省**: 可降低 **50-70%** 积分消耗

#### 方案4：添加智能过滤

只在特定条件下才调用大模型：

```python
# 简单规则预判
if price_change < 0.5% and volume_change < 1.2:
    # 波动太小，不需要AI分析
    return "hold"
else:
    # 调用大模型分析
    return llm_decision()
```

**节省**: 可降低 **60-80%** 积分消耗

### 🔧 实施建议

#### 新手推荐（成本最低）

**方案组合**: 方案2 + 方案4
- 监控频率：每5分钟1次
- 添加价格波动过滤（<0.5%不调用AI）
- **预计成本**: ~0.5积分/天

#### 平衡方案（性价比高）

**方案组合**: 方案3 + 方案4
- 使用轻量模型
- 添加智能过滤
- 监控频率：每2分钟1次
- **预计成本**: ~1.5积分/天

#### 零成本方案（需要技术能力）

**方案**: 方案1（本地大模型）
- 部署 Ollama + Qwen2.5
- 完全免费，无限制使用
- 需要GPU资源（推荐8GB以上显存）

---

## 配置说明

### 项目结构

```
欧易量化交易系统/
├── src/
│   ├── graphs/
│   │   ├── state.py           # 状态定义
│   │   ├── graph.py           # 主工作流
│   │   ├── loop_graph.py      # 循环监控子图
│   │   └── nodes/             # 节点实现
│   │       ├── market_monitor_node.py
│   │       ├── asset_management_node.py
│   │       ├── strategy_decision_node.py
│   │       ├── risk_management_node.py
│   │       └── notification_node.py
│   ├── main.py                # 主入口
│   └── static/                # 前端文件
├── config/
│   ├── strategy_decision_llm_cfg.json
│   └── notification_llm_cfg.json
├── scripts/
│   ├── install_deps.sh
│   ├── test_workflow.py
│   └── deploy.sh
├── docs/
│   ├── LOCAL_USAGE_GUIDE.md
│   └── COST_OPTIMIZATION.md
├── requirements.txt
├── AGENTS.md
├── README.md
└── QUICKSTART.md
```

### 核心依赖

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

---

## 常见问题

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

### 5. 端口被占用

**查看占用端口的进程:**
```bash
lsof -ti:5000
```

**停止占用端口的进程:**
```bash
lsof -ti:5000 | xargs kill -9
```

### 6. 积分消耗过快

查看 [成本优化方案](#成本优化) 了解如何降低积分消耗

### 7. 前端页面无法访问

**检查服务是否启动:**
```bash
curl http://localhost:5000/health
```

**检查防火墙设置:**
```bash
# Linux
sudo ufw allow 5000

# macOS
# 系统偏好设置 -> 安全性与隐私 -> 防火墙
```

---

## ⚠️ 重要提示

1. **仅用于学习研究**: 本系统仅供学习交流使用
2. **不构成投资建议**: 所有交易决策需自行判断
3. **风险自负**: 量化交易存在资金损失风险
4. **需要API密钥**: 使用前需配置欧易API密钥
5. **建议模拟盘**: 强烈建议先在模拟盘测试
6. **积分消耗**: 策略决策会消耗积分（约0.005积分/次）

---

## 📞 需要帮助？

如果您遇到任何问题，可以：

1. 查看 [常见问题](#常见问题) 章节
2. 检查 [完整使用指南](#本地使用指南)
3. 查看 [成本优化方案](#成本优化)

---

## 📜 版本历史

- **v1.1.0** (2026-03-22)
  - 新增前端监控界面
  - 完善风险管理模块
  - 优化积分消耗
  - 添加多渠道通知

- **v1.0.0** (2026-03-21)
  - 初始版本发布
  - 实现基础量化交易功能
  - 支持剥头皮策略

---

**© 2026 欧易量化交易系统 | 仅用于学习研究，不构成投资建议**
