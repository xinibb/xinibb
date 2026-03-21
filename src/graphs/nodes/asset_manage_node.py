"""
资产管理节点
功能：查询账户余额和持仓信息
"""
import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import AssetManageInput, AssetManageOutput
from cozeloop.decorator import observe


# 欧易API配置
OKX_API_BASE = "https://www.okx.com"


@observe
def get_account_balance() -> Dict[str, Any]:
    """
    获取账户余额（模拟数据）
    实际使用时需要配置API Key和签名
    
    Returns:
        账户余额信息
    """
    # 注意：实际交易需要API认证
    # 这里返回模拟数据用于演示
    # 真实环境中需要实现完整的签名认证流程
    
    return {
        "totalEq": 10000.0,  # 总权益
        "isoEq": 0.0,  # 逐仓权益
        "adjEq": 10000.0,  # 权益
        "details": [
            {
                "ccy": "USDT",
                "eq": 10000.0,  # 币种总权益
                "cashBal": 10000.0,  # 币种余额
                "utime": int(time.time() * 1000)
            }
        ]
    }


@observe
def get_positions(instId: str = None) -> List[Dict[str, Any]]:
    """
    获取持仓信息（模拟数据）
    实际使用时需要配置API Key和签名
    
    Args:
        instId: 产品ID，可选，不传则返回所有持仓
    
    Returns:
        持仓列表
    """
    # 模拟数据
    # 真实环境中需要调用带认证的API
    
    return []


def asset_manage_node(
    state: AssetManageInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> AssetManageOutput:
    """
    资产管理节点
    
    title: 资产管理
    desc: 查询账户余额、持仓信息，监控资产状态
    integrations: 欧易API
    """
    ctx = runtime.context
    
    try:
        # 获取账户余额
        balance_info = get_account_balance()
        
        total_balance = balance_info.get("totalEq", 0.0)
        available_balance = total_balance  # 简化处理
        
        # 获取持仓信息
        positions = get_positions(state.trading_pair)
        
        # 计算持仓总价值
        total_position_value = sum(
            pos.get("pos", 0) * pos.get("avgPx", 0) 
            for pos in positions
        )
        
        return AssetManageOutput(
            total_balance=total_balance,
            available_balance=available_balance,
            positions=positions,
            total_position_value=total_position_value
        )
        
    except Exception as e:
        # 返回默认值
        return AssetManageOutput(
            total_balance=0.0,
            available_balance=0.0,
            positions=[],
            total_position_value=0.0
        )
