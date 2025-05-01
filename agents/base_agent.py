"""
Base agent class for Order Book Simulator.
All specific agent types will inherit from this class.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from core.order_book import Order, OrderSide, OrderType


class BaseAgent(ABC):
    """
    Abstract base class for all trading agents in the simulation.
    """
    
    def __init__(self, agent_id: str = None, name: str = None):
        """
        Initialize a new trading agent.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Human-readable name for this agent
        """
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name or f"Agent-{self.agent_id[:8]}"
        
        # Track orders and positions
        self.active_orders: Dict[str, Order] = {}  # order_id -> Order
        self.position = 0  # Net position (positive = long, negative = short)
        self.cash = 0.0  # Cash balance
        self.trades_executed = 0  # Count of trades executed
        self.volume_traded = 0  # Total volume traded
        
        # Performance tracking
        self.pnl = 0.0  # Realized P&L
        self.trade_history = []  # List of completed trades
        
    @abstractmethod
    def on_tick(self, order_book_state: Dict[str, Any], 
                tick_num: int, timestamp: float) -> List[Order]:
        """
        Called on each simulation tick to make trading decisions.
        
        Args:
            order_book_state: Current state of the order book
            tick_num: Current tick number in the simulation
            timestamp: Current timestamp
            
        Returns:
            List of orders to submit
        """
        pass
        
    @abstractmethod
    def on_trade(self, trade: Dict[str, Any]) -> None:
        """
        Called when one of the agent's orders executes.
        
        Args:
            trade: Information about the executed trade
        """
        pass
        
    def on_order_book_update(self, order_book_state: Dict[str, Any]) -> None:
        """
        Called when the order book changes.
        
        Args:
            order_book_state: Updated state of the order book
        """
        # Optional to implement in subclasses
        pass
        
    def create_limit_order(self, side: OrderSide, price: float, 
                          quantity: int, timestamp: float) -> Order:
        """
        Create a limit order.
        
        Args:
            side: Buy or sell
            price: Limit price
            quantity: Order quantity
            timestamp: Current time
            
        Returns:
            A new Order object
        """
        order = Order(
            order_id=str(uuid.uuid4()),
            side=side,
            order_type=OrderType.LIMIT,
            price=price,
            quantity=quantity,
            timestamp=timestamp,
            agent_id=self.agent_id
        )
        self.active_orders[order.order_id] = order
        return order
        
    def create_market_order(self, side: OrderSide, quantity: int, 
                           timestamp: float) -> Order:
        """
        Create a market order.
        
        Args:
            side: Buy or sell
            quantity: Order quantity
            timestamp: Current time
            
        Returns:
            A new Order object
        """
        order = Order(
            order_id=str(uuid.uuid4()),
            side=side,
            order_type=OrderType.MARKET,
            price=0.0,  # Price is ignored for market orders
            quantity=quantity,
            timestamp=timestamp,
            agent_id=self.agent_id
        )
        self.active_orders[order.order_id] = order
        return order
        
    def update_position(self, side: OrderSide, quantity: int, price: float) -> None:
        """
        Update the agent's position and cash balance after a trade.
        
        Args:
            side: Side of the trade from this agent's perspective
            quantity: Quantity traded
            price: Trade price
        """
        cost = price * quantity
        
        if side == OrderSide.BUY:
            self.position += quantity
            self.cash -= cost
        else:  # SELL
            self.position -= quantity
            self.cash += cost
            
        self.trades_executed += 1
        self.volume_traded += quantity
        
    def update_pnl(self, mark_price: float) -> float:
        """
        Calculate realized and unrealized P&L.
        
        Args:
            mark_price: Current market price for marking the position
            
        Returns:
            Total P&L (realized + unrealized)
        """
        position_value = self.position * mark_price
        total_pnl = self.cash + position_value
        
        return total_pnl
        
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an active order.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            True if order was found and removed, False otherwise
        """
        if order_id in self.active_orders:
            del self.active_orders[order_id]
            return True
        return False
        
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.name} (ID: {self.agent_id[:8]}, Pos: {self.position})"