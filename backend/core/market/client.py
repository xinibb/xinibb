"""
行情模块 - 获取市场数据

支持：
- 实时价格
- K线数据
- 市场深度
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import aiohttp
import asyncio

from backend.models.base import Ticker, Kline, Depth


logger = logging.getLogger(__name__)


class MarketClient:
    """
    行情客户端
    
    获取市场数据（支持欧易API）
    """
    
    BASE_URL = "https://www.okx.com"
    
    def __init__(self):
        """初始化行情客户端"""
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """
        获取行情数据
        
        Args:
            symbol: 交易对，如 BTC-USDT
            
        Returns:
            Ticker对象
        """
        session = await self._get_session()
        
        url = f"{self.BASE_URL}/api/v5/market/ticker?instId={symbol}"
        
        try:
            async with session.get(url) as response:
                data = await response.json()
                
                if data.get("code") != "0":
                    raise Exception(f"获取行情失败: {data.get('msg')}")
                
                ticker_data = data["data"][0]
                
                return Ticker(
                    symbol=symbol,
                    last_price=float(ticker_data["last"]),
                    high_24h=float(ticker_data["high24h"]),
                    low_24h=float(ticker_data["low24h"]),
                    volume_24h=float(ticker_data["vol24h"]),
                    change_24h=float(ticker_data["open24h"]) / float(ticker_data["last"]) - 1,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self.logger.error(f"获取行情失败: {e}")
            raise
    
    async def get_kline(
        self,
        symbol: str,
        interval: str = "1m",
        limit: int = 100
    ) -> List[Kline]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: K线周期（1m, 5m, 15m, 1H, 4H, 1D等）
            limit: 返回数量
            
        Returns:
            K线列表
        """
        session = await self._get_session()
        
        url = f"{self.BASE_URL}/api/v5/market/candles?instId={symbol}&bar={interval}&limit={limit}"
        
        try:
            async with session.get(url) as response:
                data = await response.json()
                
                if data.get("code") != "0":
                    raise Exception(f"获取K线失败: {data.get('msg')}")
                
                klines = []
                for kline_data in data.get("data", []):
                    kline = Kline(
                        symbol=symbol,
                        interval=interval,
                        open_time=datetime.fromtimestamp(int(kline_data[0]) / 1000),
                        open=float(kline_data[1]),
                        high=float(kline_data[2]),
                        low=float(kline_data[3]),
                        close=float(kline_data[4]),
                        volume=float(kline_data[5]),
                        close_time=datetime.fromtimestamp(int(kline_data[0]) / 1000)
                    )
                    klines.append(kline)
                
                return klines
                
        except Exception as e:
            self.logger.error(f"获取K线失败: {e}")
            raise
    
    async def get_depth(self, symbol: str, limit: int = 20) -> Depth:
        """
        获取市场深度
        
        Args:
            symbol: 交易对
            limit: 深度档位
            
        Returns:
            Depth对象
        """
        session = await self._get_session()
        
        url = f"{self.BASE_URL}/api/v5/market/books?instId={symbol}&sz={limit}"
        
        try:
            async with session.get(url) as response:
                data = await response.json()
                
                if data.get("code") != "0":
                    raise Exception(f"获取深度失败: {data.get('msg')}")
                
                depth_data = data["data"][0]
                
                return Depth(
                    symbol=symbol,
                    bids=[[float(b[0]), float(b[1])] for b in depth_data.get("bids", [])],
                    asks=[[float(a[0]), float(a[1])] for a in depth_data.get("asks", [])],
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self.logger.error(f"获取深度失败: {e}")
            raise
    
    async def get_tickers(self, symbols: List[str]) -> List[Ticker]:
        """
        批量获取行情
        
        Args:
            symbols: 交易对列表
            
        Returns:
            Ticker列表
        """
        tasks = [self.get_ticker(symbol) for symbol in symbols]
        return await asyncio.gather(*tasks)
    
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
