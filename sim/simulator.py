"""
Simulation engine for the Order Book Simulator.
Manages the simulation loop, agents, and order book.
"""

import time
import pandas as pd
from typing import Dict, List, Any, Optional
from collections import defaultdict

from core.order_book import OrderBook, Order, Trade, OrderSide
from core.utils import get_timestamp, export_to_csv
from agents.base_agent import BaseAgent


class Simulator:
    """
    Simulator for running order book simulations with multiple agents.
    """
    
    def __init__(self, 
                 tick_size: float = 0.01,
                 initial_price: float = 100.0,
                 log_trades: bool = True,
                 log_rejections: bool = False):
        """
        Initialize the simulator.
        
        Args:
            tick_size: Minimum price increment
            initial_price: Starting price for the simulation
            log_trades: Whether to keep a detailed trade log
            log_rejections: Whether to log rejected/partially filled orders
        """
        # Create order book
        self.order_book = OrderBook(tick_size=tick_size, log_rejections=log_rejections)
        
        # Set initial reference price
        self.initial_price = initial_price
        self.order_book.last_trade_price = initial_price
        
        # Tick and time tracking
        self.tick_num = 0
        self.start_time = None
        self.is_running = False
        self.log_trades = log_trades
        self.log_rejections = log_rejections
        
        # Agent management
        self.agents: Dict[str, BaseAgent] = {}
        
        # History tracking
        self.history = {
            'mid_price': [],
            'best_bid': [],
            'best_ask': [],
            'spread': [],
            'timestamp': [],
            'tick': []
        }
        
        # Performance stats
        self.trade_count = 0
        self.total_volume = 0
        self.matched_orders = 0
        
        # Event logs
        self.trade_log = []
        self.agent_metrics = defaultdict(list)
        
    def add_agent(self, agent: BaseAgent) -> None:
        """
        Add an agent to the simulation.
        
        Args:
            agent: The agent to add
        """
        self.agents[agent.agent_id] = agent
        
    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the simulation.
        
        Args:
            agent_id: ID of the agent to remove
            
        Returns:
            True if agent was removed, False if not found
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    def reset(self) -> None:
        """Reset the simulation to initial state."""
        # Create new order book
        self.order_book = OrderBook(tick_size=self.order_book.tick_size, log_rejections=self.log_rejections)
        self.order_book.last_trade_price = self.initial_price
        
        # Reset tick and time tracking
        self.tick_num = 0
        self.start_time = None
        self.is_running = False
        
        # Reset history and logs
        self.history = {
            'mid_price': [],
            'best_bid': [],
            'best_ask': [],
            'spread': [],
            'timestamp': [],
            'tick': []
        }
        self.trade_log = []
        self.agent_metrics = defaultdict(list)
        
        # Reset performance stats
        self.trade_count = 0
        self.total_volume = 0
        self.matched_orders = 0
        
        # Reset agent states
        for agent in self.agents.values():
            agent.position = 0
            agent.cash = 0.0
            agent.pnl = 0.0
            agent.active_orders = {}
            agent.trade_history = []
    
    def step(self) -> Dict[str, Any]:
        """
        Run a single simulation tick.
        
        Returns:
            Dictionary with tick results
        """
        timestamp = get_timestamp()
        self.tick_num += 1
        
        if self.start_time is None:
            self.start_time = timestamp
        
        # Get current order book state
        order_book_state = self.order_book.get_order_book_state()
        
        # Collect orders from all agents
        all_orders = []
        for agent in self.agents.values():
            try:
                agent_orders = agent.on_tick(order_book_state, self.tick_num, timestamp)
                if agent_orders:
                    all_orders.extend(agent_orders)
            except Exception as e:
                print(f"Error in agent {agent.name}: {str(e)}")
        
        # Process all orders
        all_trades = []
        for order in all_orders:
            trades = self.order_book.add_order(order)
            if trades:
                all_trades.extend(trades)
                self.matched_orders += 1
        
        # Update agents with trade information
        for trade in all_trades:
            trade_dict = {
                'trade_id': trade.trade_id,
                'timestamp': trade.timestamp,
                'price': trade.price,
                'quantity': trade.quantity,
                'buyer_id': trade.buyer_id,
                'seller_id': trade.seller_id,
                'aggressor_side': trade.aggressor_side
            }
            
            if self.log_trades:
                self.trade_log.append(trade_dict)
            
            # Update buyer agent
            if trade.buyer_id in self.agents:
                self.agents[trade.buyer_id].on_trade(trade_dict)
                
            # Update seller agent
            if trade.seller_id in self.agents:
                self.agents[trade.seller_id].on_trade(trade_dict)
        
        # Update stats
        self.trade_count += len(all_trades)
        self.total_volume += sum(trade.quantity for trade in all_trades)
        
        # Get updated state for history
        updated_state = self.order_book.get_order_book_state()
        
        # Record history
        self.history['mid_price'].append(updated_state.get('mid_price'))
        self.history['best_bid'].append(self.order_book.best_bid)
        self.history['best_ask'].append(self.order_book.best_ask)
        self.history['spread'].append(updated_state.get('spread'))
        self.history['timestamp'].append(timestamp)
        self.history['tick'].append(self.tick_num)
        
        # Record agent metrics
        mark_price = updated_state.get('mid_price') or updated_state.get('last_trade') or self.initial_price
        for agent_id, agent in self.agents.items():
            pnl = agent.update_pnl(mark_price)
            self.agent_metrics[agent_id].append({
                'tick': self.tick_num,
                'timestamp': timestamp,
                'position': agent.position,
                'cash': agent.cash,
                'pnl': pnl,
                'trades_executed': agent.trades_executed
            })
        
        return {
            'tick_num': self.tick_num,
            'timestamp': timestamp,
            'trades': len(all_trades),
            'volume': sum(trade.quantity for trade in all_trades),
            'mid_price': updated_state.get('mid_price'),
            'order_book': updated_state
        }
    
    def run(self, num_steps: int = 100, step_delay: float = 0.0) -> Dict[str, Any]:
        """
        Run the simulation for a specified number of steps.
        
        Args:
            num_steps: Number of ticks to simulate
            step_delay: Delay between ticks in seconds
            
        Returns:
            Dictionary with simulation results
        """
        self.is_running = True
        results = []
        
        try:
            for _ in range(num_steps):
                if not self.is_running:
                    break
                    
                result = self.step()
                results.append(result)
                
                if step_delay > 0:
                    time.sleep(step_delay)
        finally:
            self.is_running = False
        
        return {
            'steps_completed': len(results),
            'final_tick': self.tick_num,
            'trade_count': self.trade_count,
            'total_volume': self.total_volume,
            'final_mid_price': self.order_book.mid_price,
            'results': results
        }
    
    def stop(self) -> None:
        """Stop a running simulation."""
        self.is_running = False
    
    def get_history_as_dataframe(self) -> pd.DataFrame:
        """
        Get simulation history as a DataFrame.
        
        Returns:
            DataFrame with price and time history
        """
        return pd.DataFrame(self.history)
    
    def get_trade_log_as_dataframe(self) -> pd.DataFrame:
        """
        Get trade log as a DataFrame.
        
        Returns:
            DataFrame with all trades
        """
        if not self.trade_log:
            return pd.DataFrame(columns=["trade_id", "timestamp", "price", "quantity", 
                                        "buyer_id", "seller_id", "aggressor_side"])
        return pd.DataFrame(self.trade_log)
    
    def get_agent_metrics_as_dataframe(self, agent_id: str) -> Optional[pd.DataFrame]:
        """
        Get metrics for a specific agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            DataFrame with agent metrics or None if agent not found
        """
        if agent_id not in self.agent_metrics:
            return None
        return pd.DataFrame(self.agent_metrics[agent_id])
    
    def export_results(self, base_path: str) -> Dict[str, bool]:
        """
        Export simulation results to CSV files.
        
        Args:
            base_path: Base path for output files
            
        Returns:
            Dictionary with export status for each file
        """
        results = {}
        
        # Export price history
        history_df = self.get_history_as_dataframe()
        results['history'] = export_to_csv(history_df, f"{base_path}_history.csv")
        
        # Export trade log
        trade_df = self.get_trade_log_as_dataframe()
        results['trades'] = export_to_csv(trade_df, f"{base_path}_trades.csv")
        
        # Export agent metrics
        for agent_id, agent in self.agents.items():
            agent_df = self.get_agent_metrics_as_dataframe(agent_id)
            if agent_df is not None:
                agent_name = agent.name.replace(" ", "_").lower()
                results[f'agent_{agent_name}'] = export_to_csv(
                    agent_df, f"{base_path}_{agent_name}_metrics.csv"
                )
                
        # Export current order book state
        bids_df, asks_df = self.order_book.get_order_book_as_dataframe()
        results['order_book_bids'] = export_to_csv(bids_df, f"{base_path}_bids.csv")
        results['order_book_asks'] = export_to_csv(asks_df, f"{base_path}_asks.csv")
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the simulation state.
        
        Returns:
            Dictionary with simulation summary
        """
        return {
            'tick_num': self.tick_num,
            'elapsed_time': get_timestamp() - (self.start_time or get_timestamp()),
            'trade_count': self.trade_count,
            'total_volume': self.total_volume,
            'mid_price': self.order_book.mid_price,
            'best_bid': self.order_book.best_bid,
            'best_ask': self.order_book.best_ask,
            'spread': self.order_book.spread,
            'num_agents': len(self.agents),
            'agent_types': {agent.name: type(agent).__name__ for agent in self.agents.values()}
        }