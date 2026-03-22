"""
风控模块 - 风险管理

支持：
- 止损止盈检查
- 仓位控制
- 风险等级评估
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from backend.models.base import (
    Position, Account, RiskConfig, RiskStatus, OrderSide
)


logger = logging.getLogger(__name__)


class RiskManager:
    """
    风险管理器
    
    负责监控和管理交易风险
    """
    
    def __init__(self, config: Optional[RiskConfig] = None):
        """
        初始化风控管理器
        
        Args:
            config: 风控配置
        """
        self.config = config or RiskConfig()
        self.logger = logging.getLogger(__name__)
        
        # 当日盈亏跟踪
        self.daily_pnl: float = 0.0
        self.daily_start: date = date.today()
    
    def check_position_limit(
        self,
        current_positions: List[Position],
        account: Account
    ) -> Dict[str, Any]:
        """
        检查仓位限制
        
        Args:
            current_positions: 当前持仓列表
            account: 账户信息
            
        Returns:
            检查结果
        """
        # 计算总持仓价值
        total_position_value = sum(
            pos.amount * pos.current_price 
            for pos in current_positions
        )
        
        # 计算仓位比例
        position_ratio = total_position_value / account.total_equity if account.total_equity > 0 else 0
        
        # 检查是否超过限制
        exceeded = position_ratio > self.config.max_position_ratio
        
        return {
            "passed": not exceeded,
            "position_ratio": position_ratio,
            "max_ratio": self.config.max_position_ratio,
            "message": f"仓位比例 {position_ratio:.2%} {'超过' if exceeded else '未超过'} 限制 {self.config.max_position_ratio:.2%}"
        }
    
    def check_stop_loss(
        self,
        position: Position,
        current_price: float
    ) -> Dict[str, Any]:
        """
        检查止损
        
        Args:
            position: 持仓信息
            current_price: 当前价格
            
        Returns:
            检查结果
        """
        # 计算盈亏比例
        if position.side == "long":
            pnl_ratio = (current_price - position.average_price) / position.average_price
        else:
            pnl_ratio = (position.average_price - current_price) / position.average_price
        
        # 检查是否触发止损
        triggered = pnl_ratio <= -self.config.stop_loss_percent
        
        return {
            "triggered": triggered,
            "pnl_ratio": pnl_ratio,
            "stop_loss_percent": self.config.stop_loss_percent,
            "message": f"盈亏比例 {pnl_ratio:.2%}, {'触发' if triggered else '未触发'} 止损 {-self.config.stop_loss_percent:.2%}"
        }
    
    def check_take_profit(
        self,
        position: Position,
        current_price: float
    ) -> Dict[str, Any]:
        """
        检查止盈
        
        Args:
            position: 持仓信息
            current_price: 当前价格
            
        Returns:
            检查结果
        """
        # 计算盈亏比例
        if position.side == "long":
            pnl_ratio = (current_price - position.average_price) / position.average_price
        else:
            pnl_ratio = (position.average_price - current_price) / position.average_price
        
        # 检查是否触发止盈
        triggered = pnl_ratio >= self.config.take_profit_percent
        
        return {
            "triggered": triggered,
            "pnl_ratio": pnl_ratio,
            "take_profit_percent": self.config.take_profit_percent,
            "message": f"盈亏比例 {pnl_ratio:.2%}, {'触发' if triggered else '未触发'} 止盈 {self.config.take_profit_percent:.2%}"
        }
    
    def check_order_amount(self, order_amount: float) -> Dict[str, Any]:
        """
        检查订单金额
        
        Args:
            order_amount: 订单金额
            
        Returns:
            检查结果
        """
        exceeded = order_amount > self.config.max_order_amount
        
        return {
            "passed": not exceeded,
            "order_amount": order_amount,
            "max_amount": self.config.max_order_amount,
            "message": f"订单金额 ${order_amount:.2f} {'超过' if exceeded else '未超过'} 限制 ${self.config.max_order_amount:.2f}"
        }
    
    def check_daily_loss(self, pnl: float, account: Account) -> Dict[str, Any]:
        """
        检查日内亏损限制
        
        Args:
            pnl: 当日盈亏
            account: 账户信息
            
        Returns:
            检查结果
        """
        # 重置日内盈亏（新的一天）
        if date.today() != self.daily_start:
            self.daily_pnl = 0.0
            self.daily_start = date.today()
        
        # 更新日内盈亏
        self.daily_pnl += pnl
        
        # 计算亏损比例
        loss_ratio = abs(self.daily_pnl) / account.total_equity if account.total_equity > 0 else 0
        
        # 检查是否超过限制
        exceeded = self.daily_pnl < 0 and loss_ratio > self.config.max_daily_loss
        
        return {
            "exceeded": exceeded,
            "daily_pnl": self.daily_pnl,
            "loss_ratio": loss_ratio,
            "max_daily_loss": self.config.max_daily_loss,
            "message": f"当日盈亏 ${self.daily_pnl:.2f}, {'超过' if exceeded else '未超过'} 限制 {-self.config.max_daily_loss:.2%}"
        }
    
    def evaluate_risk_level(
        self,
        account: Account,
        positions: List[Position]
    ) -> RiskStatus:
        """
        评估风险等级
        
        Args:
            account: 账户信息
            positions: 持仓列表
            
        Returns:
            RiskStatus对象
        """
        warnings = []
        risk_level = "low"
        
        # 1. 检查仓位比例
        position_check = self.check_position_limit(positions, account)
        if not position_check["passed"]:
            risk_level = "high"
            warnings.append(position_check["message"])
        
        # 2. 检查持仓止损止盈
        stop_loss_triggered = False
        take_profit_triggered = False
        
        for position in positions:
            # 止损检查
            sl_check = self.check_stop_loss(position, position.current_price)
            if sl_check["triggered"]:
                stop_loss_triggered = True
                warnings.append(f"{position.symbol}: {sl_check['message']}")
            
            # 止盈检查
            tp_check = self.check_take_profit(position, position.current_price)
            if tp_check["triggered"]:
                take_profit_triggered = True
                warnings.append(f"{position.symbol}: {tp_check['message']}")
        
        # 3. 检查日内亏损
        if self.daily_pnl < 0:
            loss_ratio = abs(self.daily_pnl) / account.total_equity
            if loss_ratio > self.config.max_daily_loss * 0.5:
                risk_level = "medium" if risk_level == "low" else risk_level
                warnings.append(f"日内亏损接近限制: {loss_ratio:.2%}")
        
        # 计算仓位比例
        total_position_value = sum(
            pos.amount * pos.current_price 
            for pos in positions
        )
        position_ratio = total_position_value / account.total_equity if account.total_equity > 0 else 0
        
        return RiskStatus(
            risk_level=risk_level,
            position_ratio=position_ratio,
            daily_pnl=self.daily_pnl,
            stop_loss_triggered=stop_loss_triggered,
            take_profit_triggered=take_profit_triggered,
            warnings=warnings
        )
