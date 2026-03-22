"""
数据模型 - 定义系统的核心数据结构
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== 枚举类型 ====================

class OrderSide(str, Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """订单类型"""
    MARKET = "market"  # 市价单
    LIMIT = "limit"    # 限价单


class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "pending"        # 待提交
    SUBMITTED = "submitted"    # 已提交
    PARTIAL = "partial"        # 部分成交
    FILLED = "filled"          # 完全成交
    CANCELLED = "cancelled"    # 已撤单
    FAILED = "failed"          # 失败


class TradeMode(str, Enum):
    """交易模式"""
    SIMULATED = "simulated"  # 模拟交易
    OKX = "okx"              # 真实交易（欧易）


class PositionSide(str, Enum):
    """持仓方向"""
    LONG = "long"   # 多头
    SHORT = "short" # 空头


# ==================== 订单模型 ====================

class Order(BaseModel):
    """订单模型"""
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="交易对，如 BTC-USDT")
    side: OrderSide = Field(..., description="买卖方向")
    order_type: OrderType = Field(..., description="订单类型")
    price: Optional[float] = Field(None, description="限价单价格")
    amount: float = Field(..., description="数量")
    filled_amount: float = Field(default=0.0, description="已成交数量")
    average_price: float = Field(default=0.0, description="成交均价")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="订单状态")
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime = Field(default_factory=datetime.now, description="更新时间")
    fee: float = Field(default=0.0, description="手续费")
    fee_currency: str = Field(default="USDT", description="手续费币种")
    client_oid: Optional[str] = Field(None, description="客户端订单ID")
    
    class Config:
        use_enum_values = True


class OrderCreate(BaseModel):
    """创建订单请求"""
    symbol: str = Field(..., description="交易对")
    side: OrderSide = Field(..., description="买卖方向")
    order_type: OrderType = Field(..., description="订单类型")
    price: Optional[float] = Field(None, description="限价单价格（市价单可为空）")
    amount: float = Field(..., gt=0, description="数量")
    
    class Config:
        use_enum_values = True


class OrderQuery(BaseModel):
    """订单查询参数"""
    symbol: Optional[str] = Field(None, description="交易对")
    status: Optional[OrderStatus] = Field(None, description="订单状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(default=100, le=500, description="返回数量限制")


# ==================== 持仓模型 ====================

class Position(BaseModel):
    """持仓模型"""
    symbol: str = Field(..., description="交易对")
    side: PositionSide = Field(..., description="持仓方向")
    amount: float = Field(..., description="持仓数量")
    available: float = Field(..., description="可用数量")
    average_price: float = Field(..., description="持仓均价")
    current_price: float = Field(default=0.0, description="当前价格")
    unrealized_pnl: float = Field(default=0.0, description="未实现盈亏")
    realized_pnl: float = Field(default=0.0, description="已实现盈亏")
    margin: float = Field(default=0.0, description="保证金")
    liquidation_price: Optional[float] = Field(None, description="强平价格")
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        use_enum_values = True


# ==================== 账户模型 ====================

class Balance(BaseModel):
    """账户余额"""
    currency: str = Field(..., description="币种")
    available: float = Field(default=0.0, description="可用余额")
    frozen: float = Field(default=0.0, description="冻结余额")
    total: float = Field(default=0.0, description="总余额")
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 8)  # 保留8位小数
        }


class Account(BaseModel):
    """账户信息"""
    account_id: str = Field(..., description="账户ID")
    balances: List[Balance] = Field(default=[], description="余额列表")
    total_equity: float = Field(default=0.0, description="总权益（USDT）")
    total_margin: float = Field(default=0.0, description="总保证金")
    total_unrealized_pnl: float = Field(default=0.0, description="总未实现盈亏")
    total_realized_pnl: float = Field(default=0.0, description="总已实现盈亏")
    update_time: datetime = Field(default_factory=datetime.now, description="更新时间")


# ==================== 行情模型 ====================

class Ticker(BaseModel):
    """行情数据"""
    symbol: str = Field(..., description="交易对")
    last_price: float = Field(..., description="最新价")
    high_24h: float = Field(default=0.0, description="24小时最高价")
    low_24h: float = Field(default=0.0, description="24小时最低价")
    volume_24h: float = Field(default=0.0, description="24小时成交量")
    change_24h: float = Field(default=0.0, description="24小时涨跌幅")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class Kline(BaseModel):
    """K线数据"""
    symbol: str = Field(..., description="交易对")
    interval: str = Field(..., description="K线周期")
    open_time: datetime = Field(..., description="开盘时间")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    close_time: datetime = Field(..., description="收盘时间")


class Depth(BaseModel):
    """深度数据"""
    symbol: str = Field(..., description="交易对")
    bids: List[List[float]] = Field(default=[], description="买单深度 [[价格, 数量], ...]")
    asks: List[List[float]] = Field(default=[], description="卖单深度 [[价格, 数量], ...]")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


# ==================== 风控模型 ====================

class RiskConfig(BaseModel):
    """风控配置"""
    max_position_ratio: float = Field(default=0.3, description="最大仓位比例")
    stop_loss_percent: float = Field(default=0.02, description="止损百分比")
    take_profit_percent: float = Field(default=0.05, description="止盈百分比")
    max_daily_loss: float = Field(default=0.1, description="单日最大亏损")
    max_order_amount: float = Field(default=10000.0, description="单笔最大金额")


class RiskStatus(BaseModel):
    """风控状态"""
    risk_level: str = Field(default="low", description="风险等级: low/medium/high")
    position_ratio: float = Field(default=0.0, description="当前仓位比例")
    daily_pnl: float = Field(default=0.0, description="当日盈亏")
    stop_loss_triggered: bool = Field(default=False, description="止损是否触发")
    take_profit_triggered: bool = Field(default=False, description="止盈是否触发")
    warnings: List[str] = Field(default=[], description="风险警告")


# ==================== 交易记录模型 ====================

class Trade(BaseModel):
    """成交记录"""
    trade_id: str = Field(..., description="成交ID")
    order_id: str = Field(..., description="订单ID")
    symbol: str = Field(..., description="交易对")
    side: OrderSide = Field(..., description="买卖方向")
    price: float = Field(..., description="成交价格")
    amount: float = Field(..., description="成交数量")
    fee: float = Field(default=0.0, description="手续费")
    fee_currency: str = Field(default="USDT", description="手续费币种")
    timestamp: datetime = Field(default_factory=datetime.now, description="成交时间")
    
    class Config:
        use_enum_values = True


# ==================== 系统配置模型 ====================

class SystemConfig(BaseModel):
    """系统配置"""
    trade_mode: TradeMode = Field(default=TradeMode.SIMULATED, description="交易模式")
    default_symbol: str = Field(default="BTC-USDT", description="默认交易对")
    initial_capital: float = Field(default=10000.0, description="初始资金（模拟）")
    enable_notification: bool = Field(default=False, description="是否启用通知")
    notification_channels: List[str] = Field(default=[], description="通知渠道")
    
    class Config:
        use_enum_values = True


# ==================== API响应模型 ====================

class ApiResponse(BaseModel):
    """API响应基类"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(default="", description="消息")
    data: Optional[Any] = Field(None, description="数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(default=False, description="是否成功")
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
