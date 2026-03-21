"""
风险管理节点
功能：监控持仓风险，执行止损止盈
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import RiskManageInput, RiskManageOutput
from cozeloop.decorator import observe


def calculate_position_ratio(
    positions: List[Dict[str, Any]],
    total_balance: float
) -> float:
    """
    计算仓位比例
    
    Args:
        positions: 持仓列表
        total_balance: 总余额
    
    Returns:
        仓位比例
    """
    if total_balance <= 0:
        return 0.0
    
    total_position_value = sum(
        abs(pos.get("pos", 0)) * pos.get("avgPx", 0)
        for pos in positions
    )
    
    return total_position_value / total_balance


def check_stop_loss(
    positions: List[Dict[str, Any]],
    current_price: float,
    stop_loss_percent: float
) -> bool:
    """
    检查是否需要止损
    
    Args:
        positions: 持仓列表
        current_price: 当前价格
        stop_loss_percent: 止损百分比
    
    Returns:
        是否需要止损
    """
    for pos in positions:
        avg_price = pos.get("avgPx", 0)
        pos_side = pos.get("posSide", "net")
        
        if avg_price <= 0:
            continue
        
        # 计算盈亏比例
        if pos.get("pos", 0) > 0:  # 多头
            loss_percent = (avg_price - current_price) / avg_price
        else:  # 空头
            loss_percent = (current_price - avg_price) / avg_price
        
        if loss_percent >= stop_loss_percent:
            return True
    
    return False


def check_take_profit(
    positions: List[Dict[str, Any]],
    current_price: float,
    take_profit_percent: float
) -> bool:
    """
    检查是否需要止盈
    
    Args:
        positions: 持仓列表
        current_price: 当前价格
        take_profit_percent: 止盈百分比
    
    Returns:
        是否需要止盈
    """
    for pos in positions:
        avg_price = pos.get("avgPx", 0)
        
        if avg_price <= 0:
            continue
        
        # 计算盈利比例
        if pos.get("pos", 0) > 0:  # 多头
            profit_percent = (current_price - avg_price) / avg_price
        else:  # 空头
            profit_percent = (avg_price - current_price) / avg_price
        
        if profit_percent >= take_profit_percent:
            return True
    
    return False


def assess_risk_level(
    position_ratio: float,
    should_stop_loss: bool,
    should_take_profit: bool,
    max_position_ratio: float
) -> str:
    """
    评估风险等级
    
    Args:
        position_ratio: 仓位比例
        should_stop_loss: 是否需要止损
        should_take_profit: 是否需要止盈
        max_position_ratio: 最大允许仓位比例
    
    Returns:
        风险等级：low/medium/high
    """
    if should_stop_loss:
        return "high"
    
    if position_ratio > max_position_ratio:
        return "high"
    
    if should_take_profit:
        return "medium"
    
    if position_ratio > max_position_ratio * 0.7:
        return "medium"
    
    return "low"


def risk_manage_node(
    state: RiskManageInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> RiskManageOutput:
    """
    风险管理节点
    
    title: 风险管理
    desc: 监控仓位风险，判断止损止盈，控制风险敞口
    integrations: 无
    """
    ctx = runtime.context
    
    try:
        # 获取风控配置
        risk_config = state.risk_config or {}
        max_position_ratio = risk_config.get("max_position_ratio", 0.3)
        stop_loss_percent = risk_config.get("stop_loss_percent", 0.02)
        take_profit_percent = risk_config.get("take_profit_percent", 0.05)
        
        # 计算仓位比例
        position_ratio = calculate_position_ratio(
            state.positions,
            state.total_balance
        )
        
        # 检查止损
        should_stop_loss = check_stop_loss(
            state.positions,
            state.current_price,
            stop_loss_percent
        )
        
        # 检查止盈
        should_take_profit = check_take_profit(
            state.positions,
            state.current_price,
            take_profit_percent
        )
        
        # 评估风险等级
        risk_level = assess_risk_level(
            position_ratio,
            should_stop_loss,
            should_take_profit,
            max_position_ratio
        )
        
        # 生成预警消息
        alert_messages = []
        
        if should_stop_loss:
            alert_messages.append("⚠️ 触发止损线，建议立即平仓")
        
        if should_take_profit:
            alert_messages.append("🎯 达到止盈目标，建议获利了结")
        
        if position_ratio > max_position_ratio:
            alert_messages.append(f"⚠️ 仓位过重({position_ratio:.1%})，超过最大限制({max_position_ratio:.1%})")
        
        alert_message = " | ".join(alert_messages) if alert_messages else "风险状态正常"
        
        return RiskManageOutput(
            risk_level=risk_level,
            should_stop_loss=should_stop_loss,
            should_take_profit=should_take_profit,
            position_ratio=position_ratio,
            alert_message=alert_message
        )
        
    except Exception as e:
        return RiskManageOutput(
            risk_level="high",
            should_stop_loss=False,
            should_take_profit=False,
            position_ratio=0.0,
            alert_message=f"风险管理异常: {str(e)}"
        )
