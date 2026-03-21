"""
循环监控子图
功能：持续监控行情并执行交易策略
"""
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    GlobalState,
    MarketMonitorInput,
    MarketMonitorOutput,
    AssetManageInput,
    AssetManageOutput,
    StrategyDecisionInput,
    StrategyDecisionOutput,
    TradeExecuteInput,
    TradeExecuteOutput,
    RiskManageInput,
    RiskManageOutput,
    NotificationInput,
    NotificationOutput,
    ShouldTradeInput,
)

from graphs.nodes.market_monitor_node import market_monitor_node
from graphs.nodes.asset_manage_node import asset_manage_node
from graphs.nodes.strategy_decision_node import strategy_decision_node
from graphs.nodes.trade_execute_node import trade_execute_node
from graphs.nodes.risk_manage_node import risk_manage_node
from graphs.nodes.notification_node import notification_node


def should_trade(state: ShouldTradeInput) -> str:
    """
    条件判断：是否应该执行交易
    
    title: 是否执行交易
    desc: 根据交易信号和风险等级判断是否应该执行交易
    """
    # 如果风险等级为高，不执行交易
    if state.risk_level == "high":
        return "不交易"
    
    # 如果信号为hold，不执行交易
    if state.trade_signal == "hold":
        return "不交易"
    
    # 否则执行交易
    return "执行交易"


# 创建子图状态
class LoopState(GlobalState):
    """循环监控子图状态"""
    pass


# 创建子图
loop_builder = StateGraph(
    LoopState,
    input_schema=GlobalState,
    output_schema=GlobalState
)


# 定义节点包装函数
def monitor_market(state: GlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> dict:
    """行情监控包装节点"""
    result = market_monitor_node(
        MarketMonitorInput(trading_pair=state.trading_pair),
        config,
        runtime
    )
    return {
        "current_price": result.current_price,
        "kline_data": result.kline_data,
        "market_trend": result.market_trend,
        "last_update_time": result.timestamp
    }


def manage_asset(state: GlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> dict:
    """资产管理包装节点"""
    result = asset_manage_node(
        AssetManageInput(trading_pair=state.trading_pair),
        config,
        runtime
    )
    return {
        "total_balance": result.total_balance,
        "available_balance": result.available_balance,
        "positions": result.positions,
        "total_position_value": result.total_position_value
    }


def decide_strategy(state: GlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> dict:
    """策略决策包装节点"""
    result = strategy_decision_node(
        StrategyDecisionInput(
            current_price=state.current_price,
            kline_data=state.kline_data,
            available_balance=state.available_balance,
            positions=state.positions,
            trading_pair=state.trading_pair
        ),
        config,
        runtime
    )
    return {
        "trade_signal": result.trade_signal,
        "signal_strength": result.signal_strength,
        "suggested_quantity": result.suggested_quantity,
        "suggested_price": result.suggested_price
    }


def manage_risk(state: GlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> dict:
    """风险管理包装节点"""
    result = risk_manage_node(
        RiskManageInput(
            positions=state.positions,
            total_balance=state.total_balance,
            current_price=state.current_price,
            risk_config=config.get("metadata", {}).get("risk_config", {})
        ),
        config,
        runtime
    )
    return {
        "risk_level": result.risk_level,
        "should_stop_loss": result.should_stop_loss,
        "should_take_profit": result.should_take_profit,
        "position_ratio": result.position_ratio
    }


def execute_trade(state: GlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> dict:
    """交易执行包装节点"""
    result = trade_execute_node(
        TradeExecuteInput(
            trade_signal=state.trade_signal,
            suggested_quantity=state.suggested_quantity,
            suggested_price=state.suggested_price,
            trading_pair=state.trading_pair
        ),
        config,
        runtime
    )
    return {
        "order_id": result.order_id,
        "order_status": result.order_status,
        "filled_quantity": result.filled_quantity,
        "avg_price": result.avg_price
    }


def send_notification(state: GlobalState, config: RunnableConfig, runtime: Runtime[Context]) -> dict:
    """通知推送包装节点"""
    # 构建通知内容
    title = f"交易信号: {state.trade_signal.upper()}"
    message = f"""
交易对: {state.trading_pair}
当前价格: {state.current_price} USDT
信号强度: {state.signal_strength:.2%}
建议操作: {state.trade_signal}
建议数量: {state.suggested_quantity}
建议价格: {state.suggested_price}
风险等级: {state.risk_level}

决策理由: {getattr(state, 'reason', 'N/A')}
时间: {state.last_update_time}
    """
    
    result = notification_node(
        NotificationInput(
            title=title,
            message=message,
            notification_config=config.get("metadata", {}).get("notification_config", {}),
            priority="high" if state.trade_signal != "hold" else "normal"
        ),
        config,
        runtime
    )
    return {
        "notification_sent": result.success,
        "notification_channels": result.channels
    }


def check_should_trade(state: GlobalState) -> str:
    """判断是否应该交易"""
    return should_trade(ShouldTradeInput(
        trade_signal=state.trade_signal,
        risk_level=state.risk_level
    ))


# 添加节点到子图
loop_builder.add_node("market_monitor", monitor_market)
loop_builder.add_node("asset_manage", manage_asset)
loop_builder.add_node("strategy_decision", decide_strategy, metadata={
    "type": "agent",
    "llm_cfg": "config/strategy_decision_cfg.json"
})
loop_builder.add_node("risk_manage", manage_risk)
loop_builder.add_node("trade_execute", execute_trade)
loop_builder.add_node("send_notification", send_notification)

# 设置入口点
loop_builder.set_entry_point("market_monitor")

# 添加边
loop_builder.add_edge("market_monitor", "asset_manage")
loop_builder.add_edge("asset_manage", "strategy_decision")
loop_builder.add_edge("strategy_decision", "risk_manage")

# 添加条件分支
loop_builder.add_conditional_edges(
    source="risk_manage",
    path=check_should_trade,
    path_map={
        "执行交易": "trade_execute",
        "不交易": "send_notification"
    }
)

loop_builder.add_edge("trade_execute", "send_notification")
loop_builder.add_edge("send_notification", END)

# 编译子图
monitoring_subgraph = loop_builder.compile()
