"""
欧易量化交易工作流 - 状态定义
包含全局状态、图输入输出、各节点独立输入输出定义
"""
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from utils.file.file import File
from datetime import datetime


# ==================== 全局状态定义 ====================
class GlobalState(BaseModel):
    """量化交易全局状态"""
    # 交易配置
    trading_pair: str = Field(default="BTC-USDT", description="交易对")
    strategy_type: str = Field(default="scalping", description="策略类型")
    
    # 行情数据
    current_price: float = Field(default=0.0, description="当前价格")
    kline_data: List[Dict[str, Any]] = Field(default=[], description="K线数据")
    market_trend: str = Field(default="", description="市场趋势")
    
    # 账户信息
    total_balance: float = Field(default=0.0, description="总余额")
    available_balance: float = Field(default=0.0, description="可用余额")
    frozen_balance: float = Field(default=0.0, description="冻结余额")
    
    # 持仓信息
    positions: List[Dict[str, Any]] = Field(default=[], description="持仓列表")
    total_position_value: float = Field(default=0.0, description="持仓总价值")
    
    # 交易信号
    trade_signal: str = Field(default="", description="交易信号：buy/sell/hold")
    signal_strength: float = Field(default=0.0, description="信号强度 0-1")
    suggested_quantity: float = Field(default=0.0, description="建议交易数量")
    suggested_price: float = Field(default=0.0, description="建议交易价格")
    
    # 订单信息
    order_id: str = Field(default="", description="订单ID")
    order_status: str = Field(default="", description="订单状态")
    filled_quantity: float = Field(default=0.0, description="已成交数量")
    avg_price: float = Field(default=0.0, description="成交均价")
    
    # 风控状态
    risk_level: str = Field(default="low", description="风险等级：low/medium/high")
    should_stop_loss: bool = Field(default=False, description="是否需要止损")
    should_take_profit: bool = Field(default=False, description="是否需要止盈")
    position_ratio: float = Field(default=0.0, description="仓位比例")
    
    # 通知信息
    notification_sent: bool = Field(default=False, description="是否已发送通知")
    notification_channels: List[str] = Field(default=[], description="已发送的渠道列表")
    
    # 运行状态
    is_running: bool = Field(default=True, description="是否继续运行")
    last_update_time: str = Field(default="", description="最后更新时间")
    error_message: str = Field(default="", description="错误信息")


# ==================== 图输入输出定义 ====================
class GraphInput(BaseModel):
    """工作流输入"""
    trading_pair: str = Field(default="BTC-USDT", description="交易对，如BTC-USDT")
    initial_capital: float = Field(default=10000.0, description="初始资金(USDT)")
    strategy_type: str = Field(default="scalping", description="策略类型")
    risk_config: Dict[str, Any] = Field(
        default={
            "max_position_ratio": 0.3,  # 最大仓位比例
            "stop_loss_percent": 0.02,  # 止损百分比 2%
            "take_profit_percent": 0.05,  # 止盈百分比 5%
            "max_daily_loss": 0.1,  # 最大日亏损 10%
        },
        description="风控配置"
    )
    notification_config: Dict[str, Any] = Field(
        default={
            "enable_email": True,
            "enable_wechat": False,
            "enable_feishu": False,
        },
        description="通知配置"
    )


class GraphOutput(BaseModel):
    """工作流输出"""
    status: str = Field(default="success", description="执行状态")
    message: str = Field(default="", description="执行消息")
    total_profit: float = Field(default=0.0, description="总收益")
    profit_rate: float = Field(default=0.0, description="收益率")
    trade_count: int = Field(default=0, description="交易次数")
    last_trade_time: str = Field(default="", description="最后交易时间")
    risk_level: str = Field(default="low", description="当前风险等级")


# ==================== 各节点独立输入输出定义 ====================

# 1. 行情监控节点
class MarketMonitorInput(BaseModel):
    """行情监控节点输入"""
    trading_pair: str = Field(..., description="交易对")


class MarketMonitorOutput(BaseModel):
    """行情监控节点输出"""
    current_price: float = Field(..., description="当前价格")
    kline_data: List[Dict[str, Any]] = Field(default=[], description="K线数据")
    market_trend: str = Field(default="", description="市场趋势")
    timestamp: str = Field(default="", description="时间戳")


# 2. 资产管理节点
class AssetManageInput(BaseModel):
    """资产管理节点输入"""
    trading_pair: str = Field(..., description="交易对")


class AssetManageOutput(BaseModel):
    """资产管理节点输出"""
    total_balance: float = Field(default=0.0, description="总余额")
    available_balance: float = Field(default=0.0, description="可用余额")
    positions: List[Dict[str, Any]] = Field(default=[], description="持仓列表")
    total_position_value: float = Field(default=0.0, description="持仓总价值")


# 3. 策略决策节点（剥头皮策略）
class StrategyDecisionInput(BaseModel):
    """策略决策节点输入"""
    current_price: float = Field(..., description="当前价格")
    kline_data: List[Dict[str, Any]] = Field(default=[], description="K线数据")
    available_balance: float = Field(default=0.0, description="可用余额")
    positions: List[Dict[str, Any]] = Field(default=[], description="持仓列表")
    trading_pair: str = Field(..., description="交易对")


class StrategyDecisionOutput(BaseModel):
    """策略决策节点输出"""
    trade_signal: str = Field(..., description="交易信号：buy/sell/hold")
    signal_strength: float = Field(default=0.0, description="信号强度 0-1")
    suggested_quantity: float = Field(default=0.0, description="建议交易数量")
    suggested_price: float = Field(default=0.0, description="建议交易价格")
    reason: str = Field(default="", description="决策理由")


# 4. 交易执行节点
class TradeExecuteInput(BaseModel):
    """交易执行节点输入"""
    trade_signal: str = Field(..., description="交易信号")
    suggested_quantity: float = Field(default=0.0, description="建议交易数量")
    suggested_price: float = Field(default=0.0, description="建议交易价格")
    trading_pair: str = Field(..., description="交易对")


class TradeExecuteOutput(BaseModel):
    """交易执行节点输出"""
    order_id: str = Field(default="", description="订单ID")
    order_status: str = Field(default="", description="订单状态")
    filled_quantity: float = Field(default=0.0, description="已成交数量")
    avg_price: float = Field(default=0.0, description="成交均价")
    message: str = Field(default="", description="执行消息")


# 5. 风险管理节点
class RiskManageInput(BaseModel):
    """风险管理节点输入"""
    positions: List[Dict[str, Any]] = Field(default=[], description="持仓列表")
    total_balance: float = Field(default=0.0, description="总余额")
    current_price: float = Field(default=0.0, description="当前价格")
    risk_config: Dict[str, Any] = Field(default={}, description="风控配置")


class RiskManageOutput(BaseModel):
    """风险管理节点输出"""
    risk_level: str = Field(default="low", description="风险等级")
    should_stop_loss: bool = Field(default=False, description="是否需要止损")
    should_take_profit: bool = Field(default=False, description="是否需要止盈")
    position_ratio: float = Field(default=0.0, description="仓位比例")
    alert_message: str = Field(default="", description="预警消息")


# 6. 通知推送节点
class NotificationInput(BaseModel):
    """通知推送节点输入"""
    title: str = Field(..., description="通知标题")
    message: str = Field(..., description="通知内容")
    notification_config: Dict[str, Any] = Field(default={}, description="通知配置")
    priority: str = Field(default="normal", description="优先级：low/normal/high")


class NotificationOutput(BaseModel):
    """通知推送节点输出"""
    success: bool = Field(default=False, description="是否成功")
    channels: List[str] = Field(default=[], description="已发送渠道列表")
    message: str = Field(default="", description="发送结果消息")


# 7. 条件判断节点输入
class ShouldTradeInput(BaseModel):
    """是否应该交易的判断输入"""
    trade_signal: str = Field(..., description="交易信号")
    risk_level: str = Field(default="low", description="风险等级")


class ShouldContinueInput(BaseModel):
    """是否继续运行的判断输入"""
    risk_level: str = Field(default="low", description="风险等级")
    should_stop_loss: bool = Field(default=False, description="是否需要止损")
    error_message: str = Field(default="", description="错误信息")


# ==================== 主图节点独立出入参定义 ====================

# 初始化节点
class InitStateInput(BaseModel):
    """初始化节点输入"""
    trading_pair: str = Field(default="BTC-USDT", description="交易对")
    strategy_type: str = Field(default="scalping", description="策略类型")


class InitStateOutput(BaseModel):
    """初始化节点输出"""
    is_running: bool = Field(default=True, description="是否继续运行")
    last_update_time: str = Field(default="", description="最后更新时间")
    error_message: str = Field(default="", description="错误信息")


# 监控循环节点
class MonitoringLoopInput(BaseModel):
    """监控循环节点输入"""
    trading_pair: str = Field(default="BTC-USDT", description="交易对")
    initial_capital: float = Field(default=10000.0, description="初始资金")
    risk_config: Dict[str, Any] = Field(default={}, description="风控配置")
    notification_config: Dict[str, Any] = Field(default={}, description="通知配置")


class MonitoringLoopOutput(BaseModel):
    """监控循环节点输出"""
    current_price: float = Field(default=0.0, description="当前价格")
    trade_signal: str = Field(default="hold", description="交易信号")
    risk_level: str = Field(default="low", description="风险等级")
    total_balance: float = Field(default=0.0, description="总余额")
    is_running: bool = Field(default=True, description="是否继续运行")
    error_message: str = Field(default="", description="错误信息")


# 生成报告节点
class GenerateReportInput(BaseModel):
    """生成报告节点输入"""
    total_balance: float = Field(default=0.0, description="总余额")
    initial_capital: float = Field(default=10000.0, description="初始资金")


class GenerateReportOutput(BaseModel):
    """生成报告节点输出"""
    status: str = Field(default="success", description="执行状态")
    message: str = Field(default="", description="执行消息")
    total_profit: float = Field(default=0.0, description="总收益")
    profit_rate: float = Field(default=0.0, description="收益率")
    trade_count: int = Field(default=0, description="交易次数")
    last_trade_time: str = Field(default="", description="最后交易时间")
    risk_level: str = Field(default="low", description="当前风险等级")
