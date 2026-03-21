"""
欧易量化交易工作流 - 主图编排
功能：协调各节点执行量化交易流程
"""
import os
import json
from datetime import datetime
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context

from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput,
    NotificationInput,
    InitStateInput,
    InitStateOutput,
    MonitoringLoopInput,
    MonitoringLoopOutput,
    GenerateReportInput,
    GenerateReportOutput,
)

from graphs.loop_graph import monitoring_subgraph


# ==================== 主图节点函数 ====================

def init_state(state: InitStateInput, config: RunnableConfig, runtime: Runtime[Context]) -> InitStateOutput:
    """
    初始化状态节点
    
    title: 初始化
    desc: 初始化交易参数和配置
    integrations: 无
    """
    return InitStateOutput(
        is_running=True,
        last_update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        error_message=""
    )


def run_monitoring_loop(state: MonitoringLoopInput, config: RunnableConfig, runtime: Runtime[Context]) -> MonitoringLoopOutput:
    """
    运行监控循环节点
    
    title: 监控循环
    desc: 调用子图执行行情监控和交易决策
    integrations: 欧易API、大语言模型
    """
    try:
        # 构建子图输入
        subgraph_input = {
            "trading_pair": state.trading_pair,
            "risk_config": state.risk_config,
            "notification_config": state.notification_config
        }
        
        # 调用监控子图
        result = monitoring_subgraph.invoke(
            subgraph_input,
            config=config
        )
        
        return MonitoringLoopOutput(
            current_price=result.get("current_price", 0.0),
            trade_signal=result.get("trade_signal", "hold"),
            risk_level=result.get("risk_level", "low"),
            total_balance=result.get("total_balance", 0.0),
            is_running=result.get("is_running", True),
            error_message=result.get("error_message", "")
        )
        
    except Exception as e:
        return MonitoringLoopOutput(
            current_price=0.0,
            trade_signal="hold",
            risk_level="high",
            total_balance=0.0,
            is_running=False,
            error_message=f"监控循环执行失败: {str(e)}"
        )


def generate_report(state: GenerateReportInput, config: RunnableConfig, runtime: Runtime[Context]) -> GenerateReportOutput:
    """
    生成交易报告节点
    
    title: 生成报告
    desc: 生成交易结果报告和收益统计
    integrations: 无
    """
    # 计算收益（简化版）
    profit = state.total_balance - state.initial_capital
    profit_rate = (profit / state.initial_capital) * 100 if state.initial_capital > 0 else 0.0
    
    return GenerateReportOutput(
        status="success",
        message="交易监控完成",
        total_profit=profit,
        profit_rate=profit_rate,
        trade_count=0,
        last_trade_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        risk_level="low"
    )


def should_continue(state: GlobalState) -> str:
    """
    条件判断：是否继续运行
    
    title: 是否继续运行
    desc: 根据风险等级和错误状态判断是否继续监控
    """
    # 如果有严重错误，停止运行
    if state.error_message and "严重" in state.error_message:
        return "停止运行"
    
    # 如果风险等级为高且触发止损，停止运行
    if state.risk_level == "high" and state.should_stop_loss:
        return "停止运行"
    
    # 否则继续运行
    return "继续运行"


# 注意：循环逻辑由子图内部处理，主图执行一次完整流程


# ==================== 主图编排 ====================

# 创建主图
builder = StateGraph(
    GlobalState,
    input_schema=GraphInput,
    output_schema=GraphOutput
)

# 添加节点
builder.add_node("init", init_state)
builder.add_node("monitoring_loop", run_monitoring_loop, metadata={"type": "loopcond"})
builder.add_node("generate_report", generate_report)

# 设置入口点
builder.set_entry_point("init")

# 添加边
builder.add_edge("init", "monitoring_loop")
builder.add_edge("monitoring_loop", "generate_report")
builder.add_edge("generate_report", END)

# 编译主图
main_graph = builder.compile()
