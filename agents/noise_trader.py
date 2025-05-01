"""
Noise Trader agent implementation.

Noise traders represent random market participants who submit
orders with little or no strategy, creating market noise.
"""

import numpy as np
from typing import Dict, List, Any, Optional

from core.order_book import Order, OrderSide, OrderType
from core.utils import random_price_near, round_to_tick
from agents.base_agent import BaseAgent


class NoiseTrader(BaseAgent):
    """
    Noise trader that generates random orders with no particular strategy.
    """
    
    def __init__(self, 
                 agent_id: str = None,
                 name: str = None,
                 order_rate: float = 0.1,  # Probability of order per tick
                 limit_order_prob: float = 0.7,  # Probability of limit vs market
                 price_range_factor: float = 0.02,  # Max distance from mid price
                 cancel_rate: float = 0.2,  # Probability of cancelling an order
                 size_range: tuple = (1, 10),  # Min/max order size
                 tick_size: float = 0.01):
        """
        Initialize a noise trader agent.
        
        Args:
            agent_id: Unique identifier
            name: Display name
            order_rate: Probability of submitting an order on each tick
            limit_order_prob: Probability of submitting limit vs market order
            price_range_factor: Max price distance from mid as a factor
            cancel_rate: Probability of cancelling an order per tick
            size_range: (min, max) order size
            tick_size: Minimum price increment
        """
        super().__init__(agent_id, name or "NoiseTrader")
        self.order_rate = order_rate
        self.limit_order_prob = limit_order_prob
        self.price_range_factor = price_range_factor
        self.cancel_rate = cancel_rate
        self.size_range = size_range
        self.tick_size = tick_size
        
    def on_tick(self, order_book_state: Dict[str, Any], 
                tick_num: int, timestamp: float) -> List[Order]:
        """
        Generate random trading activity.
        
        Args:
            order_book_state: Current state of the order book
            tick_num: Current tick number in the simulation
            timestamp: Current timestamp
            
        Returns:
            List of orders to submit
        """
        orders_to_submit = []
        
        # Maybe cancel an existing order
        self._maybe_cancel_order()
        
        # Decide whether to submit a new order
        if np.random.random() > self.order_rate:
            return []  # No new order this tick
            
        # Get reference price (mid price or last trade)
        reference_price = order_book_state.get('mid_price') 
        if reference_price is None:
            reference_price = order_book_state.get('last_trade')
            if reference_price is None:
                # No reference price to work with
                return []
                
        # Randomly choose side (buy/sell)
        side = OrderSide.BUY if np.random.random() < 0.5 else OrderSide.SELL
        
        # Randomly determine order size
        min_size, max_size = self.size_range
        quantity = np.random.randint(min_size, max_size + 1)
        
        # Decide between limit and market order
        if np.random.random() < self.limit_order_prob:
            # Create limit order with random price
            price_range = reference_price * self.price_range_factor
            
            # For buy orders, price is generally below reference; for sell above
            if side == OrderSide.BUY:
                price_offset = -np.random.random() * price_range
            else:
                price_offset = np.random.random() * price_range
                
            # Add some noise to occasionally cross the spread
            if np.random.random() < 0.1:  # 10% chance to flip the sign
                price_offset = -price_offset
                
            price = round_to_tick(reference_price + price_offset, self.tick_size)
            
            # Ensure price is positive
            price = max(self.tick_size, price)
            
            order = self.create_limit_order(
                side=side,
                price=price,
                quantity=quantity,
                timestamp=timestamp
            )
        else:
            # Create market order
            order = self.create_market_order(
                side=side,
                quantity=quantity,
                timestamp=timestamp
            )
            
        orders_to_submit.append(order)
        return orders_to_submit
        
    def _maybe_cancel_order(self) -> None:
        """Randomly cancel an existing order."""
        if not self.active_orders or np.random.random() > self.cancel_rate:
            return
            
        # Choose a random order to cancel
        order_id = np.random.choice(list(self.active_orders.keys()))
        self.cancel_order(order_id)
        
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
            # Remove the order from active_orders
            if 'order_id' in trade and trade['order_id'] in self.active_orders:
                del self.active_orders[trade['order_id']]
        elif trade['seller_id'] == self.agent_id:
            # We sold
            self.update_position(OrderSide.SELL, trade['quantity'], trade['price'])
            # Remove the order from active_orders
            if 'order_id' in trade and trade['order_id'] in self.active_orders:
                del self.active_orders[trade['order_id']]
            
        # Add to trade history
        self.trade_history.append(trade)