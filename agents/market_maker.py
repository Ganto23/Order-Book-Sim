"""
Market Maker agent implementation.

Market makers quote on both sides of the book, continuously updating
their quotes based on market conditions, and aim to earn the spread.
"""

import numpy as np
from typing import Dict, List, Any, Optional

from core.order_book import Order, OrderSide, OrderType
from core.utils import round_to_tick
from agents.base_agent import BaseAgent


class MarketMaker(BaseAgent):
    """
    Market maker agent that quotes on both sides of the book and tries
    to earn the spread while managing inventory risk.
    """
    
    def __init__(self, 
                 agent_id: str = None,
                 name: str = None,
                 quote_spread: float = 0.05,  # Base spread to quote 
                 quote_volume: int = 10,      # Volume per quote
                 max_position: int = 100,     # Max inventory allowed
                 inventory_skew_factor: float = 0.01,  # How much to skew quotes based on inventory
                 tick_size: float = 0.01,
                 skew_quotes: bool = True):
        """
        Initialize a market maker agent.
        
        Args:
            agent_id: Unique identifier
            name: Display name
            quote_spread: Default spread to quote around mid price
            quote_volume: Volume to quote on each side
            max_position: Maximum absolute position allowed
            inventory_skew_factor: How much to adjust quotes based on inventory
            tick_size: Minimum price increment
            skew_quotes: Whether to adjust quotes based on inventory
        """
        super().__init__(agent_id, name or "MarketMaker")
        self.quote_spread = quote_spread
        self.quote_volume = quote_volume
        self.max_position = max_position
        self.inventory_skew_factor = inventory_skew_factor
        self.tick_size = tick_size
        self.skew_quotes = skew_quotes
        
        # Track current quotes
        self.current_bid_id = None
        self.current_ask_id = None
        self.current_bid_price = None
        self.current_ask_price = None
        
    def on_tick(self, order_book_state: Dict[str, Any], 
                tick_num: int, timestamp: float) -> List[Order]:
        """
        Update quotes on each tick.
        
        Args:
            order_book_state: Current state of the order book
            tick_num: Current tick number in the simulation
            timestamp: Current timestamp
            
        Returns:
            List of orders to submit (new quotes)
        """
        orders_to_submit = []
        
        # First, cancel existing quotes
        self._cancel_existing_quotes()
        
        # Check if we have a midprice to work with
        mid_price = order_book_state.get('mid_price')
        if mid_price is None:
            if order_book_state.get('last_trade') is not None:
                # Use last trade price as reference if available
                mid_price = order_book_state['last_trade']
            else:
                # No reference price available, use default price
                mid_price = 100.0
        
        # Calculate quote prices with inventory skew
        bid_price, ask_price = self._calculate_quote_prices(mid_price)
        
        # Check position limits to see if we should quote on both sides
        can_buy = self.position < self.max_position
        can_sell = self.position > -self.max_position
        
        # Create new quotes
        if can_buy:
            bid_order = self.create_limit_order(
                side=OrderSide.BUY,
                price=bid_price,
                quantity=self.quote_volume,
                timestamp=timestamp
            )
            orders_to_submit.append(bid_order)
            self.current_bid_id = bid_order.order_id
            self.current_bid_price = bid_price
            
        if can_sell:
            ask_order = self.create_limit_order(
                side=OrderSide.SELL,
                price=ask_price,
                quantity=self.quote_volume,
                timestamp=timestamp
            )
            orders_to_submit.append(ask_order)
            self.current_ask_id = ask_order.order_id
            self.current_ask_price = ask_price
            
        return orders_to_submit
        
    def _calculate_quote_prices(self, mid_price: float) -> tuple:
        """
        Calculate bid and ask prices based on mid price and inventory.
        
        Args:
            mid_price: Current mid price
            
        Returns:
            Tuple of (bid_price, ask_price)
        """
        # Base spread around mid price
        half_spread = self.quote_spread / 2
        
        # Adjust prices based on inventory if skew_quotes is enabled
        inventory_skew = 0
        if self.skew_quotes:
            # Skew quotes based on current position
            inventory_skew = self.position * self.inventory_skew_factor
        
        # Calculate raw prices
        bid_price = mid_price - half_spread - inventory_skew
        ask_price = mid_price + half_spread - inventory_skew
        
        # Round to tick size
        bid_price = round_to_tick(bid_price, self.tick_size)
        ask_price = round_to_tick(ask_price, self.tick_size)
        
        # Ensure minimum spread of one tick
        if ask_price - bid_price < self.tick_size:
            if inventory_skew >= 0:
                ask_price = bid_price + self.tick_size
            else:
                bid_price = ask_price - self.tick_size
                
        return bid_price, ask_price
        
    def _cancel_existing_quotes(self) -> None:
        """Cancel any existing quotes."""
        if self.current_bid_id:
            self.cancel_order(self.current_bid_id)
            self.current_bid_id = None
            self.current_bid_price = None
            
        if self.current_ask_id:
            self.cancel_order(self.current_ask_id)
            self.current_ask_id = None
            self.current_ask_price = None
    
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
            self.current_bid_id = None  # Our bid was filled
        elif trade['seller_id'] == self.agent_id:
            # We sold
            self.update_position(OrderSide.SELL, trade['quantity'], trade['price'])
            self.current_ask_id = None  # Our ask was filled
            
        # Add to trade history
        self.trade_history.append(trade)