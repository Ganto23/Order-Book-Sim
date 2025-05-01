"""
Order Book implementation for a limit order book simulator.
This module handles the core matching engine functionality and order book structure.
"""

import heapq
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import time
import uuid


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"


@dataclass
class Order:
    """Represents an order in the order book."""
    order_id: str
    side: OrderSide
    order_type: OrderType
    price: float  # For market orders, this is None or used as limit price
    quantity: int
    timestamp: float
    agent_id: str
    
    # For priority queue based on price-time priority
    def __lt__(self, other):
        if self.side == OrderSide.BUY:
            # For buy orders, higher prices have higher priority
            if self.price != other.price:
                return self.price > other.price
            return self.timestamp < other.timestamp
        else:
            # For sell orders, lower prices have higher priority
            if self.price != other.price:
                return self.price < other.price
            return self.timestamp < other.timestamp
    
    def __hash__(self):
        return hash(self.order_id)
    
    def __eq__(self, other):
        if not isinstance(other, Order):
            return False
        return self.order_id == other.order_id


@dataclass
class Trade:
    """Represents a trade that has occurred."""
    trade_id: str
    timestamp: float
    price: float
    quantity: int
    buyer_id: str
    seller_id: str
    aggressor_side: OrderSide  # Which side initiated the trade


class OrderBook:
    """
    Implements a limit order book with price-time priority and matching engine.
    """
    
    def __init__(self, tick_size: float = 0.01, log_rejections: bool = False):
        # Order queues sorted by price-time priority
        self.buy_orders: List[Order] = []
        self.sell_orders: List[Order] = []
        
        # Order lookup by ID for fast access
        self.orders_by_id: Dict[str, Order] = {}
        
        # Price levels for quick access
        self.buy_levels: Dict[float, List[Order]] = {}  # Price -> Orders at that price
        self.sell_levels: Dict[float, List[Order]] = {}  # Price -> Orders at that price
        
        # Book stats
        self.last_trade_price: Optional[float] = None
        self.trades: List[Trade] = []
        
        # Configuration
        self.tick_size = tick_size
        self.log_rejections = log_rejections

    @property
    def best_bid(self) -> Optional[float]:
        """Returns the highest buy price in the book."""
        if self.buy_orders:
            return self.buy_orders[0].price
        return None

    @property
    def best_ask(self) -> Optional[float]:
        """Returns the lowest sell price in the book."""
        if self.sell_orders:
            return self.sell_orders[0].price
        return None

    @property
    def mid_price(self) -> Optional[float]:
        """Returns the mid-price between best bid and ask."""
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return self.last_trade_price

    @property
    def spread(self) -> Optional[float]:
        """Returns the spread between best bid and ask."""
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None

    def add_order(self, order: Order) -> List[Trade]:
        """
        Adds an order to the book and processes any matches.
        Returns a list of trades that occurred.
        """
        # Generate order ID if not provided
        if not hasattr(order, 'order_id') or not order.order_id:
            order.order_id = str(uuid.uuid4())
            
        # Set timestamp if not provided
        if not hasattr(order, 'timestamp') or not order.timestamp:
            order.timestamp = time.time()
            
        # Process based on order type
        if order.order_type == OrderType.MARKET:
            return self._process_market_order(order)
        else:  # LIMIT order
            return self._process_limit_order(order)

    def _process_market_order(self, order):
        """Process a market order by matching with existing orders."""
        executed_qty = 0
        trades = []  # Track trades to return
        
        if order.side == OrderSide.BUY:
            # Filter out orders from the same agent (avoid self-trades)
            valid_sell_orders = [o for o in self.sell_orders if o.agent_id != order.agent_id]
            
            # Keep track of orders to be removed after matching
            orders_to_remove = set()
            
            # Match with existing sell orders
            while valid_sell_orders and order.quantity > executed_qty:
                # Get the best price (lowest ask)
                matching_order = min(valid_sell_orders, key=lambda o: (o.price, o.timestamp))
                
                # Calculate trade quantity
                trade_qty = min(matching_order.quantity, order.quantity - executed_qty)
                
                # Execute the trade
                trade = self._execute_trade_simple(matching_order, order, trade_qty, matching_order.price)
                trades.append(trade)
                executed_qty += trade_qty
                
                # Update the matched order quantity
                matching_order.quantity -= trade_qty
                
                # If the matching order is fully filled, mark it for removal
                if matching_order.quantity == 0:
                    orders_to_remove.add(matching_order)
                    # Remove from valid_sell_orders to avoid re-processing
                    valid_sell_orders.remove(matching_order)
            
            # Now safely remove all fully filled orders
            for order_to_remove in orders_to_remove:
                if order_to_remove in self.sell_orders:
                    self.sell_orders.remove(order_to_remove)
                
                # Update price levels and orders_by_id
                if order_to_remove.order_id in self.orders_by_id:
                    del self.orders_by_id[order_to_remove.order_id]
                
                if order_to_remove.price in self.sell_levels:
                    if order_to_remove in self.sell_levels[order_to_remove.price]:
                        self.sell_levels[order_to_remove.price].remove(order_to_remove)
                    
                    if not self.sell_levels[order_to_remove.price]:
                        del self.sell_levels[order_to_remove.price]
                        
        else:  # SELL order
            # Filter out orders from the same agent (avoid self-trades)
            valid_buy_orders = [o for o in self.buy_orders if o.agent_id != order.agent_id]
            
            # Keep track of orders to be removed after matching
            orders_to_remove = set()
            
            # Match with existing buy orders
            while valid_buy_orders and order.quantity > executed_qty:
                # Get the best price (highest bid)
                matching_order = max(valid_buy_orders, key=lambda o: (o.price, -o.timestamp))
                
                # Calculate trade quantity
                trade_qty = min(matching_order.quantity, order.quantity - executed_qty)
                
                # Execute the trade
                trade = self._execute_trade_simple(order, matching_order, trade_qty, matching_order.price)
                trades.append(trade)
                executed_qty += trade_qty
                
                # Update the matched order quantity
                matching_order.quantity -= trade_qty
                
                # If the matching order is fully filled, mark it for removal
                if matching_order.quantity == 0:
                    orders_to_remove.add(matching_order)
                    # Remove from valid_buy_orders to avoid re-processing
                    valid_buy_orders.remove(matching_order)
            
            # Now safely remove all fully filled orders
            for order_to_remove in orders_to_remove:
                if order_to_remove in self.buy_orders:
                    self.buy_orders.remove(order_to_remove)
                
                # Update price levels and orders_by_id
                if order_to_remove.order_id in self.orders_by_id:
                    del self.orders_by_id[order_to_remove.order_id]
                
                if order_to_remove.price in self.buy_levels:
                    if order_to_remove in self.buy_levels[order_to_remove.price]:
                        self.buy_levels[order_to_remove.price].remove(order_to_remove)
                    
                    if not self.buy_levels[order_to_remove.price]:
                        del self.buy_levels[order_to_remove.price]
        
        # Update the book state after processing
        self._update_book_state()
        
        # If didn't execute the full quantity, indicate partial fill
        if executed_qty < order.quantity:
            order.quantity -= executed_qty
            if self.log_rejections:
                print(f"Market Order partially filled: {executed_qty} / {order.quantity + executed_qty}")
        
        return trades

    def _process_limit_order(self, order):
        """Process a limit order by matching with existing orders or adding to book."""
        executed_qty = 0
        trades = []  # Track trades to return
        
        # If it's a marketable limit order (can be executed immediately)
        if order.side == OrderSide.BUY and self.sell_orders and order.price >= self.sell_orders[0].price:
            # Filter out orders from the same agent (avoid self-trades)
            valid_sell_orders = [o for o in self.sell_orders 
                               if o.agent_id != order.agent_id and order.price >= o.price]
            
            # Keep track of orders to be removed after matching
            orders_to_remove = set()
            
            # Match with existing sell orders
            while valid_sell_orders and order.quantity > executed_qty:
                # Get the best price (lowest ask)
                matching_order = min(valid_sell_orders, key=lambda o: (o.price, o.timestamp))
                
                # Calculate trade quantity
                trade_qty = min(matching_order.quantity, order.quantity - executed_qty)
                
                # Execute the trade
                trade = self._execute_trade_simple(matching_order, order, trade_qty, matching_order.price)
                trades.append(trade)
                executed_qty += trade_qty
                
                # Update the matched order quantity
                matching_order.quantity -= trade_qty
                
                # If the matching order is fully filled, mark it for removal
                if matching_order.quantity == 0:
                    orders_to_remove.add(matching_order)
                    # Remove from valid_sell_orders to avoid re-processing
                    valid_sell_orders.remove(matching_order)
                
            # Now safely remove all fully filled orders
            for order_to_remove in orders_to_remove:
                if order_to_remove in self.sell_orders:
                    self.sell_orders.remove(order_to_remove)
                
                # Update price levels and orders_by_id
                if order_to_remove.order_id in self.orders_by_id:
                    del self.orders_by_id[order_to_remove.order_id]
                
                if order_to_remove.price in self.sell_levels:
                    if order_to_remove in self.sell_levels[order_to_remove.price]:
                        self.sell_levels[order_to_remove.price].remove(order_to_remove)
                    
                    if not self.sell_levels[order_to_remove.price]:
                        del self.sell_levels[order_to_remove.price]
        
        elif order.side == OrderSide.SELL and self.buy_orders and order.price <= self.buy_orders[0].price:
            # Filter out orders from the same agent (avoid self-trades)
            valid_buy_orders = [o for o in self.buy_orders 
                              if o.agent_id != order.agent_id and order.price <= o.price]
            
            # Keep track of orders to be removed after matching
            orders_to_remove = set()
            
            # Match with existing buy orders
            while valid_buy_orders and order.quantity > executed_qty:
                # Get the best price (highest bid)
                matching_order = max(valid_buy_orders, key=lambda o: (o.price, -o.timestamp))
                
                # Calculate trade quantity
                trade_qty = min(matching_order.quantity, order.quantity - executed_qty)
                
                # Execute the trade
                trade = self._execute_trade_simple(order, matching_order, trade_qty, matching_order.price)
                trades.append(trade)
                executed_qty += trade_qty
                
                # Update the matched order quantity
                matching_order.quantity -= trade_qty
                
                # If the matching order is fully filled, mark it for removal
                if matching_order.quantity == 0:
                    orders_to_remove.add(matching_order)
                    # Remove from valid_buy_orders to avoid re-processing
                    valid_buy_orders.remove(matching_order)
                
            # Now safely remove all fully filled orders
            for order_to_remove in orders_to_remove:
                if order_to_remove in self.buy_orders:
                    self.buy_orders.remove(order_to_remove)
                
                # Update price levels and orders_by_id
                if order_to_remove.order_id in self.orders_by_id:
                    del self.orders_by_id[order_to_remove.order_id]
                
                if order_to_remove.price in self.buy_levels:
                    if order_to_remove in self.buy_levels[order_to_remove.price]:
                        self.buy_levels[order_to_remove.price].remove(order_to_remove)
                    
                    if not self.buy_levels[order_to_remove.price]:
                        del self.buy_levels[order_to_remove.price]
        
        # Add any remaining quantity to the order book
        if order.quantity > executed_qty:
            # Update the order quantity to remaining amount
            order.quantity -= executed_qty
            
            # Add to appropriate side of the book
            if order.side == OrderSide.BUY:
                self.buy_orders.append(order)
                self.buy_orders.sort(key=lambda o: (-o.price, o.timestamp))  # Sort by price desc, time asc
                
                # Add to price level and orders_by_id
                if order.price not in self.buy_levels:
                    self.buy_levels[order.price] = []
                self.buy_levels[order.price].append(order)
                self.orders_by_id[order.order_id] = order
            else:
                self.sell_orders.append(order)
                self.sell_orders.sort(key=lambda o: (o.price, o.timestamp))  # Sort by price asc, time asc
                
                # Add to price level and orders_by_id
                if order.price not in self.sell_levels:
                    self.sell_levels[order.price] = []
                self.sell_levels[order.price].append(order)
                self.orders_by_id[order.order_id] = order
        
        # Update the book state
        self._update_book_state()
        return trades
    
    def _execute_trade_simple(self, sell_order, buy_order, quantity, price):
        """
        Execute a trade between a sell order and a buy order without modifying the book.
        Returns the trade object.
        """
        # Add explicit self-trade prevention check
        if sell_order.agent_id == buy_order.agent_id:
            # Don't execute self-trades
            return None
            
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            timestamp=time.time(),
            price=price,
            quantity=quantity,
            buyer_id=buy_order.agent_id,
            seller_id=sell_order.agent_id,
            aggressor_side=buy_order.side if buy_order.timestamp > sell_order.timestamp else sell_order.side
        )
        self.trades.append(trade)
        self.last_trade_price = price
        
        return trade

    def _update_book_state(self):
        """Update the state of the order book (e.g., recalculating best bid/ask)."""
        # This method can be used to update any derived state in the order book
        # For example, you might want to recalculate the best bid/ask prices
        
        # Currently, this method does nothing, but it's here for future use
        pass

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order by ID.
        Returns True if order was found and cancelled, False otherwise.
        """
        if order_id not in self.orders_by_id:
            return False
            
        order = self.orders_by_id[order_id]
        
        # Remove from orders_by_id
        del self.orders_by_id[order_id]
        
        # Remove from appropriate side and price level
        if order.side == OrderSide.BUY:
            self.buy_orders.remove(order)
            heapq.heapify(self.buy_orders)  # Re-heapify after removal
            
            self.buy_levels[order.price].remove(order)
            if not self.buy_levels[order.price]:
                del self.buy_levels[order.price]
        else:  # SELL
            self.sell_orders.remove(order)
            heapq.heapify(self.sell_orders)  # Re-heapify after removal
            
            self.sell_levels[order.price].remove(order)
            if not self.sell_levels[order.price]:
                del self.sell_levels[order.price]
                
        return True

    def modify_order(self, order_id: str, new_quantity: Optional[int] = None, 
                    new_price: Optional[float] = None) -> bool:
        """
        Modify an existing order.
        For price modifications, cancels and re-adds the order.
        For quantity reductions, maintains priority.
        Returns True if order was found and modified, False otherwise.
        """
        if order_id not in self.orders_by_id:
            return False
            
        order = self.orders_by_id[order_id]
        
        # Handle price change (cancel and re-add)
        if new_price is not None and new_price != order.price:
            self.cancel_order(order_id)
            new_order = Order(
                order_id=order_id,
                side=order.side,
                order_type=order.order_type,
                price=new_price,
                quantity=new_quantity if new_quantity is not None else order.quantity,
                timestamp=time.time(),  # New timestamp to lose time priority
                agent_id=order.agent_id
            )
            self.add_order(new_order)
            return True
            
        # Handle quantity change only (maintain priority)
        if new_quantity is not None:
            # Can't increase quantity without losing priority
            if new_quantity > order.quantity:
                self.cancel_order(order_id)
                new_order = Order(
                    order_id=order_id,
                    side=order.side,
                    order_type=order.order_type,
                    price=order.price,
                    quantity=new_quantity,
                    timestamp=time.time(),  # New timestamp to lose time priority
                    agent_id=order.agent_id
                )
                self.add_order(new_order)
            else:
                # Decrease quantity (maintain priority)
                order.quantity = new_quantity
                
                # Remove if quantity becomes zero
                if order.quantity == 0:
                    self.cancel_order(order_id)
            return True
            
        return True

    def get_order_book_state(self, levels: int = 10) -> dict:
        """
        Returns the current state of the order book.
        
        Args:
            levels: Number of price levels to include
            
        Returns:
            Dictionary containing bids and asks with prices and volumes
        """
        # Get sorted price levels
        bid_prices = sorted(self.buy_levels.keys(), reverse=True)[:levels]
        ask_prices = sorted(self.sell_levels.keys())[:levels]
        
        bids = []
        for price in bid_prices:
            volume = sum(order.quantity for order in self.buy_levels[price])
            bids.append({"price": price, "volume": volume})
            
        asks = []
        for price in ask_prices:
            volume = sum(order.quantity for order in self.sell_levels[price])
            asks.append({"price": price, "volume": volume})
            
        return {
            "bids": bids,
            "asks": asks,
            "mid_price": self.mid_price,
            "spread": self.spread,
            "last_trade": self.last_trade_price,
        }
        
    def get_trades_as_dataframe(self) -> pd.DataFrame:
        """Convert trades list to a pandas DataFrame."""
        if not self.trades:
            return pd.DataFrame(columns=["trade_id", "timestamp", "price", "quantity", 
                                        "buyer_id", "seller_id", "aggressor_side"])
                                        
        return pd.DataFrame([{
            "trade_id": trade.trade_id,
            "timestamp": trade.timestamp,
            "price": trade.price,
            "quantity": trade.quantity,
            "buyer_id": trade.buyer_id,
            "seller_id": trade.seller_id,
            "aggressor_side": trade.aggressor_side.value
        } for trade in self.trades])

    def get_order_book_as_dataframe(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Returns the order book as two DataFrames (bids and asks).
        Useful for visualization and analysis.
        """
        bids_data = []
        for price, orders in self.buy_levels.items():
            volume = sum(order.quantity for order in orders)
            bids_data.append({"price": price, "volume": volume})
            
        asks_data = []
        for price, orders in self.sell_levels.items():
            volume = sum(order.quantity for order in orders)
            asks_data.append({"price": price, "volume": volume})
        
        # Handle the case of empty data frames
        if bids_data:
            bids_df = pd.DataFrame(bids_data).sort_values("price", ascending=False)
        else:
            bids_df = pd.DataFrame(columns=["price", "volume"])
            
        if asks_data:
            asks_df = pd.DataFrame(asks_data).sort_values("price")
        else:
            asks_df = pd.DataFrame(columns=["price", "volume"])
        
        return bids_df, asks_df