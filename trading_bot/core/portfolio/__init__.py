"""
Portfolio Management Package for BensBot.

This package provides portfolio management functionalities:
- Capital allocation
- Dynamic rebalancing
- Risk management
"""

from trading_bot.core.portfolio.allocator import PortfolioAllocator, AllocationTarget
from trading_bot.core.portfolio.dynamic_allocator import DynamicAllocator

__all__ = [
    "PortfolioAllocator",
    "AllocationTarget",
    "DynamicAllocator"
] 