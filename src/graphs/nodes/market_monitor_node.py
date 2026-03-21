"""
行情监控节点
功能：获取欧易交易所实时行情数据
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
from graphs.state import MarketMonitorInput, MarketMonitorOutput
from cozeloop.decorator import observe


# 欧易API配置（公开接口，无需认证）
OKX_API_BASE = "https://www.okx.com"


@observe
def get_ticker(instId: str) -> Dict[str, Any]:
    """
    获取实时行情数据
    
    Args:
        instId: 产品ID，如 BTC-USDT
    
    Returns:
        行情数据字典
    """
    url = f"{OKX_API_BASE}/api/v5/market/ticker"
    params = {"instId": instId}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == "0" and data.get("data"):
            return data["data"][0]
        else:
            raise Exception(f"API返回错误: {data.get('msg', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"请求失败: {str(e)}")


@observe
def get_kline(instId: str, bar: str = "1m", limit: int = 100) -> List[Dict[str, Any]]:
    """
    获取K线数据
    
    Args:
        instId: 产品ID
        bar: K线周期，如 1m, 5m, 15m, 1H, 4H, 1D
        limit: 返回数量，最大300
    
    Returns:
        K线数据列表
    """
    url = f"{OKX_API_BASE}/api/v5/market/candles"
    params = {
        "instId": instId,
        "bar": bar,
        "limit": str(limit)
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == "0" and data.get("data"):
            # 转换数据格式
            kline_list = []
            for item in data["data"]:
                kline_list.append({
                    "timestamp": item[0],
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4]),
                    "volume": float(item[5]),
                    "volume_currency": float(item[6]) if len(item) > 6 else 0.0
                })
            return kline_list
        else:
            return []
    except requests.exceptions.RequestException as e:
        raise Exception(f"获取K线数据失败: {str(e)}")


def analyze_trend(kline_data: List[Dict[str, Any]]) -> str:
    """
    分析市场趋势
    
    Args:
        kline_data: K线数据列表
    
    Returns:
        趋势描述：上涨/下跌/震荡
    """
    if not kline_data or len(kline_data) < 10:
        return "数据不足"
    
    # 取最近10根K线
    recent_data = kline_data[:10]
    
    # 计算简单移动平均
    closes = [k["close"] for k in recent_data]
    ma5 = sum(closes[:5]) / 5
    ma10 = sum(closes) / 10
    
    # 判断趋势
    if closes[0] > ma5 > ma10:
        return "强势上涨"
    elif closes[0] > ma5:
        return "上涨"
    elif closes[0] < ma5 < ma10:
        return "强势下跌"
    elif closes[0] < ma5:
        return "下跌"
    else:
        return "震荡"


def market_monitor_node(
    state: MarketMonitorInput,
    config: RunnableConfig,
    runtime: Runtime[Context]
) -> MarketMonitorOutput:
    """
    行情监控节点
    
    title: 行情监控
    desc: 获取欧易交易所实时价格、K线数据并分析市场趋势
    integrations: 欧易API
    """
    ctx = runtime.context
    
    try:
        # 获取实时行情
        ticker = get_ticker(state.trading_pair)
        current_price = float(ticker.get("last", 0))
        
        # 获取K线数据
        kline_data = get_kline(state.trading_pair, bar="1m", limit=100)
        
        # 分析趋势
        market_trend = analyze_trend(kline_data)
        
        # 时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return MarketMonitorOutput(
            current_price=current_price,
            kline_data=kline_data[:20],  # 只保留最近20根
            market_trend=market_trend,
            timestamp=timestamp
        )
        
    except Exception as e:
        # 返回默认值
        return MarketMonitorOutput(
            current_price=0.0,
            kline_data=[],
            market_trend="获取失败",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
