"""
Aggressive Trader agent implementation.

Aggressive traders take liquidity from the market by submitting market orders
or crossing the spread with marketable limit orders.
"""

import numpy as np
from typing import Dict, List, Any, Optional

from core.order_book import Order, OrderSide, OrderType
from agents.base_agent import BaseAgent


class AggressiveTrader(BaseAgent):
    """
    Aggressive trader that takes liquidity from the market using market orders.
    """
    
    def __init__(self, 
                 agent_id: str = None,
                 name: str = None,
                 order_rate: float = 0.2,  # Probability of order per tick
                 trade_size_range: tuple = (1, 20),  # Min/max order size
                 max_position: int = 100,  # Max position allowed
                 position_influence: float = 0.5):  # How much position affects order direction
        """
        Initialize an aggressive trader agent.
        
        Args:
            agent_id: Unique identifier
            name: Display name
            order_rate: Probability of submitting an order on each tick
            trade_size_range: (min, max) order size
            max_position: Maximum absolute position allowed
            position_influence: How much current position influences order direction
        """
        super().__init__(agent_id, name or "AggressiveTrader")
        self.order_rate = order_rate
        self.trade_size_range = trade_size_range
        self.max_position = max_position
        self.position_influence = position_influence
        
    def on_tick(self, order_book_state: Dict[str, Any], 
                tick_num: int, timestamp: float) -> List[Order]:
        """
        Decide whether to submit an aggressive order.
        
        Args:
            order_book_state: Current state of the order book
            tick_num: Current tick number in the simulation
            timestamp: Current timestamp
            
        Returns:
            List of orders to submit
        """
        orders_to_submit = []
        
        # Decide whether to trade on this tick
        if np.random.random() > self.order_rate:
            return []  # No trading this tick
            
        # Check if we have data to work with
        if not order_book_state.get('bids') and not order_book_state.get('asks'):
            return []  # No liquidity to take
            
        # Determine direction with position influence
        base_probability = 0.5  # Base 50/50 chance of buy/sell
        position_adjustment = (self.position / self.max_position) * self.position_influence
        
        # Adjust probability - more likely to sell when long, buy when short
        buy_probability = base_probability - position_adjustment
        
        # Ensure probability stays within [0, 1]
        buy_probability = max(0, min(1, buy_probability))
        
        # Determine side
        side = OrderSide.BUY if np.random.random() < buy_probability else OrderSide.SELL
        
        # Check if we exceed position limits
        if (side == OrderSide.BUY and self.position >= self.max_position) or \
           (side == OrderSide.SELL and self.position <= -self.max_position):
            # Can't take more position in this direction
            return []
            
        # Check if there's liquidity to take
        if side == OrderSide.BUY and not order_book_state.get('asks'):
            return []  # No asks to hit
        if side == OrderSide.SELL and not order_book_state.get('bids'):
            return []  # No bids to hit
            
        # Randomly determine order size
        min_size, max_size = self.trade_size_range
        quantity = np.random.randint(min_size, max_size + 1)
        
        # Create market order
        order = self.create_market_order(
            side=side,
            quantity=quantity,
            timestamp=timestamp
        )
        orders_to_submit.append(order)
        
        return orders_to_submit
        
    def on_trade(self, trade: Dict[str, Any]) -> None:
        """
        Handle a completed trade.
        
        Args:
            trade: Information about the executed trade
        """
        # Update position and cash
        if trade['buyer_id'] == self.agent_id:
            # We bought
            self.update_position(OrderSide.BUY, trade['quantity'], trade['price'])
        elif trade['seller_id'] == self.agent_id:
            # We sold
            self.update_position(OrderSide.SELL, trade['quantity'], trade['price'])
            
        # Add to trade history
        self.trade_history.append(trade)