"""
真实交易模块 - 欧易OKX交易所

严格按照OKX API规范实现交易功能
"""
import hashlib
import hmac
import base64
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import logging
import asyncio
import aiohttp

from backend.models.base import (
    Order, OrderCreate, OrderStatus, OrderSide, OrderType,
    Position, PositionSide, Account, Balance, Trade, TradeMode
)
from backend.core.trading.base import BaseTrader


logger = logging.getLogger(__name__)


class OKXTrader(BaseTrader):
    """
    欧易真实交易实现
    
    API文档: https://www.okx.com/docs-v5/zh/
    
    支持的功能：
    - 现货交易
    - 合约交易
    - 账户查询
    - 订单管理
    """
    
    # API基础URL
    BASE_URL = "https://www.okx.com"
    
    # API端点
    ENDPOINTS = {
        # 账户
        "account_balance": "/api/v5/account/balance",
        "positions": "/api/v5/account/positions",
        
        # 订单
        "create_order": "/api/v5/trade/order",
        "cancel_order": "/api/v5/trade/cancel-order",
        "order_info": "/api/v5/trade/order",
        "orders_pending": "/api/v5/trade/orders-pending",
        "orders_history": "/api/v5/trade/orders-history",
        
        # 成交记录
        "fills": "/api/v5/trade/fills",
        
        # 行情
        "tickers": "/api/v5/market/tickers",
        "books": "/api/v5/market/books",
        "candles": "/api/v5/market/candles",
    }
    
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        passphrase: str,
        simulated: bool = True  # 是否使用模拟盘
    ):
        """
        初始化欧易交易器
        
        Args:
            api_key: API Key
            secret_key: Secret Key
            passphrase: API Passphrase
            simulated: 是否使用模拟盘（默认True，建议先测试）
        """
        super().__init__(TradeMode.OKX)
        
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.simulated = simulated  # 欧易的模拟盘标识
        
        # HTTP会话
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 是否使用模拟盘（欧易的sandbox环境）
        self.base_url = "https://www.okx.com"
        if simulated:
            self.base_url = "https://www.okx.com"  # 欧易模拟盘使用相同的URL，通过header区分
        
        self.logger.info(
            f"欧易交易器初始化完成，模式: {'模拟盘' if simulated else '实盘'}"
        )
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def _generate_signature(
        self,
        timestamp: str,
        method: str,
        request_path: str,
        body: str = ""
    ) -> str:
        """
        生成API签名
        
        Args:
            timestamp: 时间戳
            method: HTTP方法
            request_path: 请求路径
            body: 请求体
            
        Returns:
            签名字符串
        """
        message = timestamp + method + request_path + body
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod=hashlib.sha256
        )
        d = mac.digest()
        return base64.b64encode(d).decode('utf-8')
    
    def _get_headers(
        self,
        method: str,
        request_path: str,
        body: str = ""
    ) -> Dict[str, str]:
        """
        获取请求头
        
        Args:
            method: HTTP方法
            request_path: 请求路径
            body: 请求体
            
        Returns:
            请求头字典
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        sign = self._generate_signature(timestamp, method, request_path, body)
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': sign,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        # 模拟盘标识
        if self.simulated:
            headers['x-simulated-trading'] = '1'
        
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        body: Optional[Dict] = None
    ) -> Dict:
        """
        发送API请求
        
        Args:
            method: HTTP方法
            endpoint: 端点
            params: 查询参数
            body: 请求体
            
        Returns:
            响应数据
        """
        session = await self._get_session()
        
        url = self.base_url + endpoint
        request_path = endpoint
        
        # 构建查询字符串
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url += "?" + query_string
            request_path += "?" + query_string
        
        # 请求体
        body_str = json.dumps(body) if body else ""
        
        # 请求头
        headers = self._get_headers(method, request_path, body_str)
        
        try:
            async with session.request(
                method,
                url,
                headers=headers,
                data=body_str if body else None
            ) as response:
                data = await response.json()
                
                if response.status != 200:
                    self.logger.error(f"API请求失败: {data}")
                    raise Exception(f"API请求失败: {data.get('msg', 'Unknown error')}")
                
                return data
                
        except Exception as e:
            self.logger.error(f"API请求异常: {e}")
            raise
    
    # ==================== 订单相关 ====================
    
    async def create_order(self, order: OrderCreate) -> Order:
        """
        创建订单
        
        OKX API文档: https://www.okx.com/docs-v5/zh/#order-book-trading-trade-post-place-order
        """
        # 构建请求体
        body = {
            "instId": order.symbol,  # 产品ID，如 BTC-USDT
            "tdMode": "cash",  # 交易模式：cash现货，cross全仓，isolated逐仓
            "side": order.side.value,  # buy或sell
            "ordType": order.order_type.value,  # market市价，limit限价
            "sz": str(order.amount)  # 数量
        }
        
        # 限价单需要价格
        if order.order_type == OrderType.LIMIT and order.price:
            body["px"] = str(order.price)
        
        # 发送请求
        result = await self._request("POST", self.ENDPOINTS["create_order"], body=body)
        
        # 解析响应
        if result.get("code") != "0":
            raise Exception(f"创建订单失败: {result.get('msg')}")
        
        order_data = result["data"][0]
        
        # 返回订单对象
        return Order(
            order_id=order_data["ordId"],
            client_oid=order_data.get("clOrdId"),
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            price=order.price,
            amount=order.amount,
            status=OrderStatus.SUBMITTED,
            create_time=datetime.now()
        )
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        撤销订单
        
        OKX API文档: https://www.okx.com/docs-v5/zh/#order-book-trading-trade-post-cancel-order
        """
        body = {
            "instId": symbol,
            "ordId": order_id
        }
        
        result = await self._request("POST", self.ENDPOINTS["cancel_order"], body=body)
        
        if result.get("code") != "0":
            raise Exception(f"撤销订单失败: {result.get('msg')}")
        
        return True
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """
        查询订单
        
        OKX API文档: https://www.okx.com/docs-v5/zh/#order-book-trading-trade-get-order-details
        """
        params = {
            "instId": symbol,
            "ordId": order_id
        }
        
        result = await self._request("GET", self.ENDPOINTS["order_info"], params=params)
        
        if result.get("code") != "0":
            raise Exception(f"查询订单失败: {result.get('msg')}")
        
        if not result.get("data"):
            return None
        
        order_data = result["data"][0]
        
        # 状态映射
        status_map = {
            "live": OrderStatus.SUBMITTED,
            "partially_filled": OrderStatus.PARTIAL,
            "filled": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED
        }
        
        return Order(
            order_id=order_data["ordId"],
            symbol=order_data["instId"],
            side=OrderSide(order_data["side"]),
            order_type=OrderType(order_data["ordType"]),
            price=float(order_data.get("px", 0)),
            amount=float(order_data["sz"]),
            filled_amount=float(order_data.get("fillSz", 0)),
            average_price=float(order_data.get("avgPx", 0)),
            status=status_map.get(order_data["state"], OrderStatus.PENDING),
            fee=float(order_data.get("fee", 0)),
            fee_currency=order_data.get("feeCcy", "USDT"),
            create_time=datetime.fromisoformat(order_data["cTime"].replace("Z", "+00:00")),
            update_time=datetime.fromisoformat(order_data["uTime"].replace("Z", "+00:00"))
        )
    
    async def get_orders(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        limit: int = 100
    ) -> List[Order]:
        """
        查询订单列表
        
        OKX API文档: https://www.okx.com/docs-v5/zh/#order-book-trading-trade-get-order-list
        """
        params = {"limit": str(limit)}
        
        if symbol:
            params["instId"] = symbol
        
        result = await self._request("GET", self.ENDPOINTS["orders_pending"], params=params)
        
        if result.get("code") != "0":
            raise Exception(f"查询订单列表失败: {result.get('msg')}")
        
        orders = []
        for order_data in result.get("data", []):
            # 状态映射
            status_map = {
                "live": OrderStatus.SUBMITTED,
                "partially_filled": OrderStatus.PARTIAL,
                "filled": OrderStatus.FILLED,
                "canceled": OrderStatus.CANCELLED
            }
            
            order = Order(
                order_id=order_data["ordId"],
                symbol=order_data["instId"],
                side=OrderSide(order_data["side"]),
                order_type=OrderType(order_data["ordType"]),
                price=float(order_data.get("px", 0)),
                amount=float(order_data["sz"]),
                filled_amount=float(order_data.get("fillSz", 0)),
                average_price=float(order_data.get("avgPx", 0)),
                status=status_map.get(order_data["state"], OrderStatus.PENDING),
                create_time=datetime.fromisoformat(order_data["cTime"].replace("Z", "+00:00"))
            )
            orders.append(order)
        
        return orders
    
    # ==================== 持仓相关 ====================
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """
        查询持仓
        
        OKX API文档: https://www.okx.com/docs-v5/zh/#trading-account-get-account-positions
        """
        params = {}
        if symbol:
            params["instId"] = symbol
        
        result = await self._request("GET", self.ENDPOINTS["positions"], params=params)
        
        if result.get("code") != "0":
            raise Exception(f"查询持仓失败: {result.get('msg')}")
        
        positions = []
        for pos_data in result.get("data", []):
            position = Position(
                symbol=pos_data["instId"],
                side=PositionSide.LONG if pos_data["posSide"] == "long" else PositionSide.SHORT,
                amount=float(pos_data["pos"]),
                available=float(pos_data["availPos"]),
                average_price=float(pos_data["avgPx"]),
                unrealized_pnl=float(pos_data["upl"]),
                margin=float(pos_data["margin"]),
                liquidation_price=float(pos_data.get("liqPx", 0)) if pos_data.get("liqPx") else None
            )
            positions.append(position)
        
        return positions
    
    async def close_position(self, symbol: str, amount: Optional[float] = None) -> Order:
        """平仓"""
        # OKX平仓通过创建反向订单实现
        # 这里简化处理，实际需要查询持仓方向
        positions = await self.get_positions(symbol)
        
        if not positions:
            raise ValueError(f"无持仓: {symbol}")
        
        position = positions[0]
        close_amount = amount or position.amount
        
        # 创建反向订单
        order = OrderCreate(
            symbol=symbol,
            side=OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=close_amount
        )
        
        return await self.create_order(order)
    
    # ==================== 账户相关 ====================
    
    async def get_account(self) -> Account:
        """
        查询账户信息
        
        OKX API文档: https://www.okx.com/docs-v5/zh/#trading-account-get-account-balance
        """
        result = await self._request("GET", self.ENDPOINTS["account_balance"])
        
        if result.get("code") != "0":
            raise Exception(f"查询账户失败: {result.get('msg')}")
        
        account_data = result["data"][0]
        
        # 解析余额
        balances = []
        for bal_data in account_data.get("details", []):
            balance = Balance(
                currency=bal_data["ccy"],
                available=float(bal_data["availBal"]),
                frozen=float(bal_data["frozenBal"]),
                total=float(bal_data["cashBal"])
            )
            balances.append(balance)
        
        return Account(
            account_id=account_data["uid"],
            balances=balances,
            total_equity=float(account_data["totalEq"]),
            update_time=datetime.now()
        )
    
    async def get_balance(self, currency: str = "USDT") -> Balance:
        """查询余额"""
        account = await self.get_account()
        
        for balance in account.balances:
            if balance.currency == currency:
                return balance
        
        return Balance(currency=currency, available=0.0, frozen=0.0, total=0.0)
    
    # ==================== 成交记录 ====================
    
    async def get_trades(
        self,
        symbol: Optional[str] = None,
        order_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Trade]:
        """
        查询成交记录
        
        OKX API文档: https://www.okx.com/docs-v5/zh/#order-book-trading-trade-get-transaction-details
        """
        params = {"limit": str(limit)}
        
        if symbol:
            params["instId"] = symbol
        if order_id:
            params["ordId"] = order_id
        
        result = await self._request("GET", self.ENDPOINTS["fills"], params=params)
        
        if result.get("code") != "0":
            raise Exception(f"查询成交记录失败: {result.get('msg')}")
        
        trades = []
        for trade_data in result.get("data", []):
            trade = Trade(
                trade_id=trade_data["tradeId"],
                order_id=trade_data["ordId"],
                symbol=trade_data["instId"],
                side=OrderSide(trade_data["side"]),
                price=float(trade_data["fillPx"]),
                amount=float(trade_data["fillSz"]),
                fee=float(trade_data["fee"]),
                fee_currency=trade_data.get("feeCcy", "USDT"),
                timestamp=datetime.fromisoformat(trade_data["ts"].replace("Z", "+00:00"))
            )
            trades.append(trade)
        
        return trades
    
    # ==================== 清理 ====================
    
    async def close(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
