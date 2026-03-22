"""
交易模块 - 基础抽象类

定义统一的交易接口，所有交易实现都必须继承此类
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from backend.models.base import (
    Order, OrderCreate, OrderStatus, OrderSide,
    Position, Account, Balance, Trade, TradeMode
)


logger = logging.getLogger(__name__)


class BaseTrader(ABC):
    """
    交易基类
    
    所有交易实现（模拟、真实）都必须继承此类并实现所有抽象方法
    """
    
    def __init__(self, mode: TradeMode = TradeMode.SIMULATED):
        """
        初始化交易器
        
        Args:
            mode: 交易模式（模拟/真实）
        """
        self.mode = mode
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    # ==================== 订单相关 ====================
    
    @abstractmethod
    async def create_order(self, order: OrderCreate) -> Order:
        """
        创建订单
        
        Args:
            order: 订单创建请求
            
        Returns:
            创建的订单对象
            
        Raises:
            Exception: 创建失败时抛出异常
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        撤销订单
        
        Args:
            order_id: 订单ID
            symbol: 交易对
            
        Returns:
            是否撤销成功
        """
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Optional[Order]:
        """
        查询订单
        
        Args:
            order_id: 订单ID
            symbol: 交易对
            
        Returns:
            订单对象，不存在返回None
        """
        pass
    
    @abstractmethod
    async def get_orders(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        limit: int = 100
    ) -> List[Order]:
        """
        查询订单列表
        
        Args:
            symbol: 交易对（可选）
            status: 订单状态（可选）
            limit: 返回数量限制
            
        Returns:
            订单列表
        """
        pass
    
    # ==================== 持仓相关 ====================
    
    @abstractmethod
    async def get_positions(self, symbol: Optional[str] = None) -> List[Position]:
        """
        查询持仓
        
        Args:
            symbol: 交易对（可选，不传则返回所有持仓）
            
        Returns:
            持仓列表
        """
        pass
    
    @abstractmethod
    async def close_position(self, symbol: str, amount: Optional[float] = None) -> Order:
        """
        平仓
        
        Args:
            symbol: 交易对
            amount: 平仓数量（可选，不传则全部平仓）
            
        Returns:
            平仓订单
        """
        pass
    
    # ==================== 账户相关 ====================
    
    @abstractmethod
    async def get_account(self) -> Account:
        """
        查询账户信息
        
        Returns:
            账户对象
        """
        pass
    
    @abstractmethod
    async def get_balance(self, currency: str = "USDT") -> Balance:
        """
        查询余额
        
        Args:
            currency: 币种
            
        Returns:
            余额对象
        """
        pass
    
    # ==================== 成交记录 ====================
    
    @abstractmethod
    async def get_trades(
        self,
        symbol: Optional[str] = None,
        order_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Trade]:
        """
        查询成交记录
        
        Args:
            symbol: 交易对（可选）
            order_id: 订单ID（可选）
            limit: 返回数量限制
            
        Returns:
            成交记录列表
        """
        pass
    
    # ==================== 工具方法 ====================
    
    def _generate_order_id(self) -> str:
        """
        生成订单ID
        
        Returns:
            唯一的订单ID
        """
        import uuid
        return f"{self.mode.value}_{uuid.uuid4().hex[:16]}"
    
    def _generate_trade_id(self) -> str:
        """
        生成成交ID
        
        Returns:
            唯一的成交ID
        """
        import uuid
        return f"trade_{uuid.uuid4().hex[:16]}"
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否健康
        """
        try:
            account = await self.get_account()
            return account is not None
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
