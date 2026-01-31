"""
Core module for EvoBot Trading System
"""
from .trade_manager import TradeManager, trade_manager
from .risk_manager import RiskManager, risk_manager
from .notifier import Notifier, notifier

__all__ = [
    'TradeManager', 'trade_manager',
    'RiskManager', 'risk_manager',
    'Notifier', 'notifier'
]
