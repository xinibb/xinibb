"""
交易执行节点
功能：执行买入/卖出交易操作
"""
import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import TradeExecuteInput, TradeExecuteOutput
from cozeloop.decorator import observe


# 欧易API配置
OKX_API_BASE = "https://www.okx.com"


@observe
def place_order(
    instId: str,
    tdMode: str,
    side: str,
    ordType: str,
    sz: str,
    px: str = None
) -> Dict[str, Any]:
    """
    下单接口（模拟）
    实际使用时需要配置API Key和签名
    
    Args:
        instId: 产品ID
        tdMode: 交易模式（cross：全仓，isolated：逐仓，cash：非保证金）
        side: 订单方向（buy：买入，sell：卖出）
        ordType: 订单类型（market：市价，limit：限价）
        sz: 委托数量
        px: 委托价格（限价单必填）
    
    Returns:
        订单信息
    """
    # 注意：实际交易需要API认证
    # 这里返回模拟数据用于演示
    
    return {
        "ordId": f"mock_{int(time.time() * 1000)}",
        "clOrdId": f"client_{int(time.time() * 1000)}",
        "tag": "scalping_strategy",
        "sCode": "0",
        "sMsg": "订单提交成功"
    }


@observe
def get_order_info(instId: str, ordId: str) -> Dict[str, Any]:
    """
    查询订单信息（模拟）
    
    Args:
        instId: 产品ID
        ordId: 订单ID
    
    Returns:
        订单详情
    """
    # 模拟数据
    return {
        "ordId": ordId,
        "instId": instId,
        "tag": "scalping_strategy",
        "state": "filled",  # canceled, live, partially_filled, filled
        "fillPx": "0",
        "fillSz": "0",
        "avgPx": "0"
    }


def trade_execute_node(
    state: TradeExecuteInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> TradeExecuteOutput:
    """
    交易执行节点
    
    title: 交易执行
    desc: 根据策略信号执行买入/卖出交易
    integrations: 欧易API
    """
    ctx = runtime.context
    
    try:
        # 如果是hold信号，直接返回
        if state.trade_signal == "hold":
            return TradeExecuteOutput(
                order_id="",
                order_status="skipped",
                filled_quantity=0.0,
                avg_price=0.0,
                message="策略信号为持有，不执行交易"
            )
        
        # 验证交易数量
        if state.suggested_quantity <= 0:
            return TradeExecuteOutput(
                order_id="",
                order_status="failed",
                filled_quantity=0.0,
                avg_price=0.0,
                message="交易数量无效"
            )
        
        # 确定交易方向
        side = "buy" if state.trade_signal == "buy" else "sell"
        
        # 下单（市价单）
        order_result = place_order(
            instId=state.trading_pair,
            tdMode="cash",  # 现金模式
            side=side,
            ordType="market",  # 市价单
            sz=str(state.suggested_quantity)
        )
        
        # 检查订单状态
        if order_result.get("sCode") == "0":
            # 订单提交成功，查询订单详情
            time.sleep(0.5)  # 等待订单处理
            
            order_info = get_order_info(
                state.trading_pair,
                order_result.get("ordId", "")
            )
            
            return TradeExecuteOutput(
                order_id=order_result.get("ordId", ""),
                order_status=order_info.get("state", "unknown"),
                filled_quantity=float(order_info.get("fillSz", 0)),
                avg_price=float(order_info.get("avgPx", 0)),
                message=f"{side}订单执行成功"
            )
        else:
            return TradeExecuteOutput(
                order_id="",
                order_status="failed",
                filled_quantity=0.0,
                avg_price=0.0,
                message=f"订单提交失败: {order_result.get('sMsg', 'Unknown error')}"
            )
            
    except Exception as e:
        return TradeExecuteOutput(
            order_id="",
            order_status="error",
            filled_quantity=0.0,
            avg_price=0.0,
            message=f"交易执行异常: {str(e)}"
        )
