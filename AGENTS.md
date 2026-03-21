# 欧易量化交易工作流系统

## 项目概述
- **名称**: 欧易量化交易系统（OKX Quantitative Trading System）
- **功能**: 基于剥头皮策略的自动化量化交易工作流，支持行情监控、策略决策、风险管理、交易执行和多渠道通知

## 核心特性
- ✅ 实时行情监控（欧易API）
- ✅ 剥头皮策略分析（大语言模型驱动）
- ✅ 自动化交易执行
- ✅ 风险管理（止损/止盈/仓位控制）
- ✅ 多渠道通知推送（邮件）
- ✅ 循环监控机制

## 节点清单

| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| init_state | `graphs/graph.py` | task | 初始化交易参数和配置 | - | - |
| run_monitoring_loop | `graphs/graph.py` | loopcond | 运行监控循环，调用子图执行交易流程 | - | - |
| generate_report | `graphs/graph.py` | task | 生成交易报告和收益统计 | - | - |

### 子图节点清单（monitoring_subgraph）

| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| market_monitor | `graphs/nodes/market_monitor_node.py` | task | 获取欧易实时价格、K线数据并分析趋势 | - | - |
| asset_manage | `graphs/nodes/asset_manage_node.py` | task | 查询账户余额、持仓信息 | - | - |
| strategy_decision | `graphs/nodes/strategy_decision_node.py` | agent | 基于剥头皮策略分析行情，生成交易信号 | - | `config/strategy_decision_cfg.json` |
| risk_manage | `graphs/nodes/risk_manage_node.py` | task | 监控仓位风险，判断止损止盈 | - | - |
| trade_execute | `graphs/nodes/trade_execute_node.py` | task | 执行买入/卖出交易操作 | - | - |
| send_notification | `graphs/nodes/notification_node.py` | task | 通过邮件推送交易通知 | - | - |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 子图清单

| 子图名 | 文件位置 | 功能描述 | 被调用节点 |
|-------|---------|------|---------|
| monitoring_subgraph | `graphs/loop_graph.py` | 执行完整的交易监控流程（行情→策略→风控→交易→通知） | run_monitoring_loop |

## 技能使用

- **策略决策节点（strategy_decision）**: 使用大语言模型技能进行行情分析和交易决策
- **通知推送节点（send_notification）**: 使用邮件技能发送交易通知

## 工作流架构

```
主图流程：
init → monitoring_loop → generate_report → END

监控子图流程：
market_monitor → asset_manage → strategy_decision → risk_manage → [条件分支]
                                                           ↓
                                            ┌──────────────┴──────────────┐
                                            ↓                              ↓
                                    trade_execute                  send_notification
                                            ↓                              ↓
                                    send_notification ────────────────→ END

```

## 配置说明

### 1. 交易参数配置
```json
{
  "trading_pair": "BTC-USDT",          // 交易对
  "initial_capital": 10000.0,          // 初始资金(USDT)
  "strategy_type": "scalping"          // 策略类型
}
```

### 2. 风控参数配置
```json
{
  "max_position_ratio": 0.3,           // 最大仓位比例 30%
  "stop_loss_percent": 0.02,           // 止损百分比 2%
  "take_profit_percent": 0.05,         // 止盈百分比 5%
  "max_daily_loss": 0.1                // 最大日亏损 10%
}
```

### 3. 通知配置
```json
{
  "enable_email": true,                // 启用邮件通知
  "email_recipients": ["user@example.com"],  // 收件人列表
  "enable_wechat": false,              // 微信通知（需配置）
  "enable_feishu": false               // 飞书通知（需配置）
}
```

## 剥头皮策略说明

### 核心原则
1. **快进快出**: 持仓时间短（几分钟到几小时）
2. **小目标**: 单次利润目标 0.5%-2%
3. **高频交易**: 每日多次交易机会
4. **严格止损**: 单次亏损控制在 1% 以内
5. **顺势而为**: 跟随短期趋势方向
6. **仓位控制**: 单次交易不超过总资金的 30%

### 交易信号规则
- **BUY**: 价格触及支撑位、短期均线上穿、RSI<30回升、成交量放大
- **SELL**: 价格触及阻力位、短期均线下穿、RSI>70回落、达到目标利润
- **HOLD**: 市场信号不明确时保持观望

## 使用指南

### 1. 启动交易监控
```python
# 调用工作流
result = main_graph.invoke({
    "trading_pair": "BTC-USDT",
    "initial_capital": 10000.0,
    "strategy_type": "scalping",
    "risk_config": {...},
    "notification_config": {...}
})
```

### 2. 查看交易报告
工作流执行完成后，会返回包含以下信息的报告：
- 总收益和收益率
- 交易次数
- 当前风险等级
- 最后交易时间

### 3. 风险提示
⚠️ **重要提示**:
- 本系统仅供学习和研究使用
- 实际交易需要配置真实的API Key和签名
- 量化交易存在风险，请谨慎投资
- 建议先在模拟环境测试

## 技术栈

- **框架**: LangGraph 1.0
- **语言**: Python 3.10+
- **交易所**: 欧易（OKX）
- **AI模型**: 大语言模型（豆包/DeepSeek/Kimi）
- **通知**: 邮件（SMTP）

## 文件结构

```
src/
├── graphs/
│   ├── state.py                    # 状态定义
│   ├── graph.py                    # 主图编排
│   ├── loop_graph.py               # 循环监控子图
│   └── nodes/
│       ├── market_monitor_node.py  # 行情监控
│       ├── asset_manage_node.py    # 资产管理
│       ├── strategy_decision_node.py # 策略决策
│       ├── trade_execute_node.py   # 交易执行
│       ├── risk_manage_node.py     # 风险管理
│       └── notification_node.py    # 通知推送
config/
└── strategy_decision_cfg.json      # 策略决策模型配置
```

## 更新日志

### v1.0.0 (2026-03-20)
- ✅ 完成基础工作流搭建
- ✅ 实现剥头皮策略决策
- ✅ 集成欧易API
- ✅ 实现风险管理系统
- ✅ 集成邮件通知
- ✅ 通过测试验证

## 后续优化建议

1. **实盘交易集成**: 配置真实的欧易API Key和签名机制
2. **多币种支持**: 扩展支持多个交易对并行监控
3. **策略优化**: 引入更多技术指标和策略模式
4. **数据持久化**: 添加交易历史记录和数据分析
5. **Web界面**: 开发可视化的交易监控面板
6. **回测系统**: 实现历史数据回测功能
