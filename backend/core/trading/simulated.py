"""
模拟交易模块

实现本地模拟撮合逻辑，用于测试和演示
"""
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import asyncio
import logging

from backend.models.base import (
    Order, OrderCreate, OrderStatus, OrderSide, OrderType,
    Position, PositionSide, Account, Balance, Trade, TradeMode
)
from backend.core.trading.base import BaseTrader


logger = logging.getLogger(__name__)


class SimulatedTrader(BaseTrader):
    """
    模拟交易实现
    
    特性：
    - 本地虚拟撮合
    - 即时成交（市价单）
    - 限价单等待匹配
    - 无真实资金风险
    - 数据持久化到本地文件
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        """
        初始化模拟交易
        
        Args:
            initial_capital: 初始资金（USDT）
        """
        super().__init__(TradeMode.SIMULATED)
        
        # 数据存储路径
        self.data_dir = Path("data/simulated")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据
        self.orders: Dict[str, Order] = {}  # 订单字典
        self.positions: Dict[str, Position] = {}  # 持仓字典
        self.trades: List[Trade] = []  # 成交记录
        self.account: Account = Account(
            account_id="simulated_account_001",
            balances=[
                Balance(currency="USDT", available=initial_capital, frozen=0.0, total=initial_capital)
            ]
        )
        
        # 加载历史数据
        self._load_data()
        
        self.logger.info(f"模拟交易器初始化完成，初始资金: ${initial_capital}")
    
    # ==================== 订单相关 ====================
    
    async def create_order(self, order: OrderCreate) -> Order:
        """创建订单"""
        # 生成订单ID
        order_id = self._generate_order_id()
        
        # 创建订单对象
        new_order = Order(
            order_id=order_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            price=order.price,
            amount=order.amount,
            status=OrderStatus.SUBMITTED
        )
        
        # 检查余额
        balance = await self.get_balance("USDT")
        required = order.amount * (order.price or 0)
        
        if order.side == OrderSide.BUY and balance.available < required:
            raise ValueError(f"余额不足: 可用 {balance.available}, 需要 {required}")
        
        # 冻结资金
        if order.side == OrderSide.BUY:
            await self._freeze_balance("USDT", required)
        
        # 保存订单
        self.orders[order_id] = new_order
        
        # 市价单立即撮合
        if order.order_type == OrderType.MARKET:
            await self._match_market_order(new_order)
        else:
            # 限价单等待撮合
            self.logger.info(f"限价单已提交: {order_id}, 价格: {order.price}")
        
        # 保存数据
        self._save_data()
        
        return new_order
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """撤销订单"""
        if order_id not in self.orders:
            raise ValueError(f"订单不存在: {order_id}")
        
        order = self.orders[order_id]
        
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            raise ValueError(f"订单已成交或已撤销: {order.status}")
        
        # 解冻资金
        if order.side == OrderSide.BUY and order.price:
            frozen_amount = (order.amount - order.filled_amount) * order.price
            await self._unfreeze_balance("USDT", frozen_amount)
        
        # 更新状态
        order.status = OrderStatus.CANCELLED
        order.update_time = datetime.now()
        
        self._save_data()
        self.logger.info(f"订单已撤销: {order_id}")
        
        return True
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """查询订单"""
        return self.orders.get(order_id)
    
    async def get_orders(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        limit: int = 100
    ) -> List[Order]:
        """查询订单列表"""
        orders = list(self.orders.values())
        
        # 过滤
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        if status:
            orders = [o for o in orders if o.status == status]
        
        # 排序（最新的在前）
        orders.sort(key=lambda x: x.create_time, reverse=True)
        
        return orders[:limit]
    
    # ==================== 持仓相关 ====================
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """查询持仓"""
        positions = list(self.positions.values())
        
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
        
        # 过滤掉数量为0的持仓
        positions = [p for p in positions if p.amount > 0]
        
        return positions
    
    async def close_position(self, symbol: str, amount: Optional[float] = None) -> Order:
        """平仓"""
        if symbol not in self.positions:
            raise ValueError(f"无持仓: {symbol}")
        
        position = self.positions[symbol]
        
        if amount is None:
            amount = position.amount
        
        if amount > position.amount:
            raise ValueError(f"平仓数量超过持仓数量: {amount} > {position.amount}")
        
        # 创建平仓订单
        order = OrderCreate(
            symbol=symbol,
            side=OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=amount
        )
        
        return await self.create_order(order)
    
    # ==================== 账户相关 ====================
    
    async def get_account(self) -> Account:
        """查询账户信息"""
        return self.account
    
    async def get_balance(self, currency: str = "USDT") -> Balance:
        """查询余额"""
        for balance in self.account.balances:
            if balance.currency == currency:
                return balance
        
        # 不存在则返回0
        return Balance(currency=currency, available=0.0, frozen=0.0, total=0.0)
    
    # ==================== 成交记录 ====================
    
    async def get_trades(
        self,
        symbol: Optional[str] = None,
        order_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Trade]:
        """查询成交记录"""
        trades = self.trades
        
        # 过滤
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        if order_id:
            trades = [t for t in trades if t.order_id == order_id]
        
        # 排序（最新的在前）
        trades.sort(key=lambda x: x.timestamp, reverse=True)
        
        return trades[:limit]
    
    # ==================== 内部方法 ====================
    
    async def _match_market_order(self, order: Order):
        """
        撮合市价单
        
        注意：这里简化处理，使用固定价格成交
        实际应该从市场获取最新价格
        """
        # 获取模拟价格（实际应从市场获取）
        # 这里简化为固定价格
        mock_price = order.price or 43000.0  # 默认价格
        
        # 模拟成交
        filled_amount = order.amount
        filled_price = mock_price
        filled_value = filled_amount * filled_price
        fee = filled_value * 0.001  # 0.1% 手续费
        
        # 更新订单
        order.status = OrderStatus.FILLED
        order.filled_amount = filled_amount
        order.average_price = filled_price
        order.fee = fee
        order.update_time = datetime.now()
        
        # 扣除手续费
        if order.side == OrderSide.BUY:
            await self._unfreeze_balance("USDT", order.amount * (order.price or mock_price))
            await self._deduct_balance("USDT", fee)
        else:
            await self._deduct_balance("USDT", fee)
        
        # 记录成交
        trade = Trade(
            trade_id=self._generate_trade_id(),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            price=filled_price,
            amount=filled_amount,
            fee=fee
        )
        self.trades.append(trade)
        
        # 更新持仓
        await self._update_position(order, filled_amount, filled_price)
        
        self.logger.info(
            f"订单成交: {order.order_id}, "
            f"价格: {filled_price}, 数量: {filled_amount}, "
            f"手续费: {fee}"
        )
    
    async def _update_position(self, order: Order, amount: float, price: float):
        """更新持仓"""
        symbol = order.symbol
        
        if symbol not in self.positions:
            # 新建持仓
            position = Position(
                symbol=symbol,
                side=PositionSide.LONG if order.side == OrderSide.BUY else PositionSide.SHORT,
                amount=amount,
                available=amount,
                average_price=price
            )
            self.positions[symbol] = position
        else:
            # 更新持仓
            position = self.positions[symbol]
            
            if order.side == OrderSide.BUY:
                # 加仓
                total_value = position.amount * position.average_price + amount * price
                total_amount = position.amount + amount
                position.average_price = total_value / total_amount
                position.amount = total_amount
                position.available += amount
            else:
                # 减仓
                position.amount -= amount
                position.available -= amount
                
                # 清空持仓
                if position.amount <= 0:
                    del self.positions[symbol]
    
    async def _freeze_balance(self, currency: str, amount: float):
        """冻结余额"""
        for balance in self.account.balances:
            if balance.currency == currency:
                if balance.available < amount:
                    raise ValueError(f"可用余额不足: {balance.available} < {amount}")
                balance.available -= amount
                balance.frozen += amount
                return
        
        raise ValueError(f"币种不存在: {currency}")
    
    async def _unfreeze_balance(self, currency: str, amount: float):
        """解冻余额"""
        for balance in self.account.balances:
            if balance.currency == currency:
                balance.frozen -= amount
                balance.available += amount
                return
        
        raise ValueError(f"币种不存在: {currency}")
    
    async def _deduct_balance(self, currency: str, amount: float):
        """扣除余额"""
        for balance in self.account.balances:
            if balance.currency == currency:
                balance.total -= amount
                if balance.available >= amount:
                    balance.available -= amount
                else:
                    balance.frozen -= amount
                return
        
        raise ValueError(f"币种不存在: {currency}")
    
    # ==================== 数据持久化 ====================
    
    def _save_data(self):
        """保存数据到本地文件"""
        try:
            data = {
                "orders": {k: v.dict() for k, v in self.orders.items()},
                "positions": {k: v.dict() for k, v in self.positions.items()},
                "trades": [t.dict() for t in self.trades],
                "account": self.account.dict()
            }
            
            file_path = self.data_dir / "trading_data.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")
    
    def _load_data(self):
        """从本地文件加载数据"""
        try:
            file_path = self.data_dir / "trading_data.json"
            
            if not file_path.exists():
                self.logger.info("数据文件不存在，使用初始数据")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 恢复订单
            self.orders = {
                k: Order(**v) for k, v in data.get("orders", {}).items()
            }
            
            # 恢复持仓
            self.positions = {
                k: Position(**v) for k, v in data.get("positions", {}).items()
            }
            
            # 恢复成交记录
            self.trades = [Trade(**t) for t in data.get("trades", [])]
            
            # 恢复账户
            if "account" in data:
                self.account = Account(**data["account"])
            
            self.logger.info(
                f"数据加载成功: {len(self.orders)} 个订单, "
                f"{len(self.positions)} 个持仓, "
                f"{len(self.trades)} 条成交记录"
            )
            
        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
