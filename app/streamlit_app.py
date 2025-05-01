"""
Streamlit frontend for the Order Book Simulator.
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import sys
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import internal modules
from sim.simulator import Simulator
from sim.config import (SimulationConfig, get_default_config, 
                        get_demo_config, get_high_volatility_config, 
                        get_low_liquidity_config)
from core.order_book import OrderSide, OrderType
from agents.market_maker import MarketMaker
from agents.aggressive_trader import AggressiveTrader
from agents.noise_trader import NoiseTrader
from app.visuals import (create_depth_chart, create_price_chart, 
                         create_trades_chart, create_agent_pnl_chart,
                         create_spread_chart, create_volume_heatmap)

# Define the color palette as constants for consistent usage
COLOR_MIDNIGHT_BLUE = "#001f3d"
COLOR_NAVY_BLUE = "#045174"
COLOR_DESERT_SUN = "#d89c60"
COLOR_BURNT_ORANGE = "#e87a00"

# Set page configuration
st.set_page_config(
    page_title="Order Book Simulator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state variables
if 'simulator' not in st.session_state:
    st.session_state.simulator = None
    
if 'config' not in st.session_state:
    st.session_state.config = get_default_config()
    
if 'agent_names' not in st.session_state:
    st.session_state.agent_names = {}
    
if 'current_tick' not in st.session_state:
    st.session_state.current_tick = 0


def create_simulator(config: SimulationConfig) -> Simulator:
    """
    Create a new simulator with agents based on configuration.
    
    Args:
        config: Simulation configuration
        
    Returns:
        Configured simulator
    """
    # Create simulator
    simulator = Simulator(
        tick_size=config.tick_size,
        initial_price=config.initial_price,
        log_trades=config.log_trades,
        log_rejections=False  # Default to false to avoid console clutter
    )
    
    # Add market makers
    for i in range(config.market_makers.count):
        mm = MarketMaker(
            name=f"MM-{i+1}",
            quote_spread=config.market_makers.quote_spread,
            quote_volume=config.market_makers.quote_volume,
            max_position=config.market_makers.max_position,
            inventory_skew_factor=config.market_makers.inventory_skew_factor,
            tick_size=config.tick_size,
            skew_quotes=config.market_makers.skew_quotes
        )
        simulator.add_agent(mm)
        st.session_state.agent_names[mm.agent_id] = mm.name
    
    # Add aggressive traders
    for i in range(config.aggressive_traders.count):
        at = AggressiveTrader(
            name=f"Aggr-{i+1}",
            order_rate=config.aggressive_traders.order_rate,
            trade_size_range=(
                config.aggressive_traders.trade_size_min,
                config.aggressive_traders.trade_size_max
            ),
            max_position=config.aggressive_traders.max_position,
            position_influence=config.aggressive_traders.position_influence
        )
        simulator.add_agent(at)
        st.session_state.agent_names[at.agent_id] = at.name
    
    # Add noise traders
    for i in range(config.noise_traders.count):
        nt = NoiseTrader(
            name=f"Noise-{i+1}",
            order_rate=config.noise_traders.order_rate,
            limit_order_prob=config.noise_traders.limit_order_prob,
            price_range_factor=config.noise_traders.price_range_factor,
            cancel_rate=config.noise_traders.cancel_rate,
            size_range=(
                config.noise_traders.size_min,
                config.noise_traders.size_max
            ),
            tick_size=config.tick_size
        )
        simulator.add_agent(nt)
        st.session_state.agent_names[nt.agent_id] = nt.name
    
    return simulator


def reset_simulation():
    """Reset the simulation to initial state."""
    # Create a new simulator
    st.session_state.simulator = create_simulator(st.session_state.config)
    st.session_state.current_tick = 0


def export_results():
    """Export simulation results to CSV files."""
    if st.session_state.simulator is None:
        st.warning("No simulation data to export.")
        return
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"data/sim_{timestamp}"
    
    # Export using simulator's export function
    results = st.session_state.simulator.export_results(base_path)
    
    # Show success message with links to files
    success_count = sum(1 for success in results.values() if success)
    st.success(f"Successfully exported {success_count} files to data directory.")
    
    return results


def render_tooltip(title, content):
    """Render a tooltip with helpful information."""
    st.markdown(f"""
    <div class="tooltip">
        {title} ⓘ
        <span class="tooltiptext">{content}</span>
    </div>
    """, unsafe_allow_html=True)


def force_update_visualization():
    """Force Streamlit to update visualizations, especially useful with high tick counts."""
    # This is a workaround to ensure charts update at high tick counts
    if st.session_state.simulator is not None:
        st.session_state.current_tick = st.session_state.simulator.tick_num
        
        # Explicitly set a flag to force visualization
        st.session_state.force_viz = True


def run_simulation_step():
    """
    Run a single step of the simulation directly in the main Streamlit thread.
    This approach avoids the threading issues that can cause visualization problems.
    """
    if st.session_state.simulator is None:
        return False
    
    if st.session_state.current_tick >= st.session_state.config.max_ticks:
        st.warning("Maximum ticks reached. Reset simulation to continue.")
        return False
        
    # Run one simulation step
    result = st.session_state.simulator.step()
    st.session_state.current_tick = result['tick_num']
    return True


def main():
    """Main Streamlit application."""
    # Add custom CSS - consolidated selectors and removed redundancy
    st.markdown(f"""
    <style>
    /* Main theme colors based on the color palette */
    :root {{
        --midnight-blue: {COLOR_MIDNIGHT_BLUE};
        --navy-blue: {COLOR_NAVY_BLUE};
        --desert-sun: {COLOR_DESERT_SUN};
        --burnt-orange: {COLOR_BURNT_ORANGE};
    }}

    /* Change background and text colors */
    .stApp {{
        background-color: #f5f5f7;
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: var(--midnight-blue) !important;
    }}

    /* Style the sidebar */
    section[data-testid="stSidebar"] {{
        background-color: #f0f2f5;
        border-right: 2px solid var(--desert-sun);
    }}
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {{
        color: var(--navy-blue) !important;
        border-bottom: 1px solid var(--desert-sun);
        padding-bottom: 0.3rem;
    }}
    
    /* Style buttons */
    .stButton>button {{
        color: white;
        background-color: var(--navy-blue);
        border-radius: 5px;
        border: none;
        transition: all 0.3s ease;
    }}
    
    .stButton>button:hover {{
        background-color: var(--burnt-orange);
        transform: translateY(-2px);
    }}

    /* Style metrics */
    [data-testid="stMetricValue"] {{
        color: var(--navy-blue) !important;
        font-weight: bold !important;
    }}

    [data-testid="stMetricLabel"] {{
        color: var(--midnight-blue) !important;
    }}
    
    /* Style headers */
    .main .block-container h1,
    .main .block-container h2 {{
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--desert-sun);
    }}

    /* Style tooltips */
    .tooltip {{
        position: relative;
        display: inline-block;
        cursor: help;
        font-weight: bold;
    }}
    .tooltip .tooltiptext {{
        visibility: hidden;
        width: 300px;
        background-color: var(--midnight-blue);
        color: white;
        text-align: left;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -150px;
        opacity: 0;
        transition: opacity 0.3s;
        font-weight: normal;
        box-shadow: 0 0 10px rgba(0,0,0,0.2);
    }}
    .tooltip:hover .tooltiptext {{
        visibility: visible;
        opacity: 1;
    }}

    /* Style expanders - consolidated selectors */
    /* Expander header */
    .st-emotion-cache-1a65o5c, [data-testid="stExpander"] > div:first-child {{
        color: white !important;
        font-weight: 600;
        background-color: var(--midnight-blue) !important;
        padding: 10px 15px !important;
        border-radius: 10px 10px 0 0 !important;
    }}
    
    /* Expander content */
    .st-emotion-cache-j7qwjs, 
    [data-testid="stExpander"] details[open] div.stMarkdown,
    .element-container .stExpander details[open] .stMarkdown div {{
        background-color: var(--midnight-blue) !important;
        color: white !important;
        padding: 15px !important;
        border-radius: 0 0 10px 10px !important;
        border: 1px solid var(--desert-sun) !important;
        border-top: none !important;
    }}
    
    /* Text in expanders */
    [data-testid="stExpander"] details[open] div.stMarkdown p,
    [data-testid="stExpander"] details[open] div.stMarkdown li,
    .element-container .stExpander details[open] .stMarkdown div p,
    .element-container .stExpander details[open] .stMarkdown div li {{
        color: white !important;
    }}
    
    /* Strong/bold text in expanders */
    [data-testid="stExpander"] details[open] div.stMarkdown strong,
    [data-testid="stExpander"] details[open] div.stMarkdown b,
    .element-container .stExpander details[open] .stMarkdown div strong {{
        color: var(--desert-sun) !important;
    }}

    /* Alert styling */
    div[data-testid="stAlert"] {{
        border-color: var(--desert-sun) !important;
    }}

    .stAlert {{
        background-color: rgba(4, 81, 116, 0.1);
        border-left-color: var(--navy-blue) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("📊 Limit Order Book Simulator")
    st.markdown("""
    An interactive simulation of a limit order book with multiple agent types.
    Configure parameters, run the simulation, and view real-time market data.
    """)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Simulation Settings")
        
        # Preset configurations
        st.subheader("Preset Configurations")
        preset_options = {
            "Default": get_default_config,
            "Demo": get_demo_config,
            "High Volatility": get_high_volatility_config,
            "Low Liquidity": get_low_liquidity_config
        }
        
        preset = st.selectbox("Select Preset", list(preset_options.keys()))
        
        if st.button("Load Preset"):
            st.session_state.config = preset_options[preset]()
            # Reset simulation if one is running
            if st.session_state.simulator is not None:
                reset_simulation()
            st.success(f"Loaded {preset} configuration!")
        
        st.markdown("---")
        
        # Market Settings
        st.subheader("Market Settings")
        
        config = st.session_state.config
        
        tick_size = st.number_input(
            "Tick Size", 
            min_value=0.001, 
            max_value=1.0, 
            value=config.tick_size,
            step=0.001,
            format="%.3f"
        )
        
        initial_price = st.number_input(
            "Initial Price", 
            min_value=0.1, 
            max_value=1000.0, 
            value=config.initial_price,
            step=0.1
        )
        
        # Simulation settings
        st.subheader("Simulation Settings")
        
        max_ticks = st.number_input(
            "Max Ticks", 
            min_value=100, 
            max_value=10000, 
            value=config.max_ticks,
            step=100
        )
        
        step_delay = st.slider(
            "Tick Delay (seconds)", 
            min_value=0.0, 
            max_value=1.0, 
            value=config.step_delay,
            step=0.01
        )
        
        # Agent configurations
        st.subheader("Agent Configuration")
        
        with st.expander("Market Makers"):
            mm_count = st.slider("Count", 0, 10, config.market_makers.count)
            mm_spread = st.slider("Quote Spread", 0.01, 0.5, config.market_makers.quote_spread, 0.01)
            mm_volume = st.slider("Quote Volume", 1, 50, config.market_makers.quote_volume, 1)
            mm_inventory_skew = st.slider(
                "Inventory Skew Factor", 
                0.0, 0.1, 
                config.market_makers.inventory_skew_factor,
                0.001,
                format="%.3f"
            )
        
        with st.expander("Aggressive Traders"):
            at_count = st.slider("Count", 0, 10, config.aggressive_traders.count)
            at_rate = st.slider(
                "Order Rate", 
                0.0, 1.0, 
                config.aggressive_traders.order_rate,
                0.05
            )
            at_size_min = st.slider(
                "Min Order Size", 
                1, 20, 
                config.aggressive_traders.trade_size_min, 
                1
            )
            at_size_max = st.slider(
                "Max Order Size", 
                1, 50, 
                config.aggressive_traders.trade_size_max, 
                1
            )
        
        with st.expander("Noise Traders"):
            nt_count = st.slider("Count", 0, 20, config.noise_traders.count)
            nt_rate = st.slider(
                "Order Rate", 
                0.0, 1.0, 
                config.noise_traders.order_rate,
                0.05
            )
            nt_limit_prob = st.slider(
                "Limit Order Probability", 
                0.0, 1.0, 
                config.noise_traders.limit_order_prob,
                0.05
            )
            nt_cancel_rate = st.slider(
                "Cancel Rate", 
                0.0, 1.0, 
                config.noise_traders.cancel_rate,
                0.05
            )
        
        # Save configuration
        if st.button("Apply Settings"):
            # Update config
            config.tick_size = tick_size
            config.initial_price = initial_price
            config.max_ticks = max_ticks
            config.step_delay = step_delay
            
            # Market makers
            config.market_makers.count = mm_count
            config.market_makers.quote_spread = mm_spread
            config.market_makers.quote_volume = mm_volume
            config.market_makers.inventory_skew_factor = mm_inventory_skew
            
            # Aggressive traders
            config.aggressive_traders.count = at_count
            config.aggressive_traders.order_rate = at_rate
            config.aggressive_traders.trade_size_min = at_size_min
            config.aggressive_traders.trade_size_max = at_size_max
            
            # Noise traders
            config.noise_traders.count = nt_count
            config.noise_traders.order_rate = nt_rate
            config.noise_traders.limit_order_prob = nt_limit_prob
            config.noise_traders.cancel_rate = nt_cancel_rate
            
            # Reset simulation if one is running
            if st.session_state.simulator is not None:
                reset_simulation()
            
            st.success("Settings applied!")
            
        # Option to save config to file
        if st.button("Save Config to File"):
            os.makedirs("data", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            config_path = f"data/config_{timestamp}.json"
            if config.save(config_path):
                st.success(f"Configuration saved to {config_path}")
            else:
                st.error("Failed to save configuration")
    
    # Main content - Simulation controls and visualization
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        run_button = st.button("▶️ Run Complete Simulation", use_container_width=True)
        if run_button:
            # Create a new simulator if needed
            if 'simulator' not in st.session_state or st.session_state.simulator is None:
                st.session_state.simulator = create_simulator(st.session_state.config)
            
            # Show progress bar for the simulation
            progress_bar = st.progress(0)
            
            # Run the simulation for the specified number of steps
            max_ticks = st.session_state.config.max_ticks
            
            with st.spinner(f"Running simulation for {max_ticks} ticks..."):
                for i in range(max_ticks):
                    # Run one step
                    result = st.session_state.simulator.step()
                    # Update progress
                    progress_bar.progress((i + 1) / max_ticks)
                
                st.success(f"Simulation completed! Ran for {max_ticks} ticks.")
                # Update current tick
                st.session_state.current_tick = max_ticks
    
    with col2:
        reset_button = st.button("🔄 Reset", use_container_width=True)
        if reset_button:
            # Reset the simulator
            st.session_state.simulator = create_simulator(st.session_state.config)
            st.session_state.current_tick = 0
            st.success("Simulator reset!")
    
    with col3:
        export_button = st.button("💾 Export Data", use_container_width=True)
        if export_button:
            export_results()
    
    with col4:
        refresh_button = st.button("🔄 Refresh Charts", use_container_width=True)
        if refresh_button and st.session_state.simulator is not None:
            st.experimental_rerun()
    
    # Simulation status
    st.markdown("---")
    
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        st.subheader("Simulation Status")
        
        if st.session_state.simulator is not None:
            summary = st.session_state.simulator.get_summary()
            
            # Format metrics
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
            
            with metrics_col1:
                st.metric("Current Tick", summary['tick_num'])
            
            with metrics_col2:
                st.metric("Trades", summary['trade_count'])
            
            with metrics_col3:
                mid_price = summary['mid_price']
                if mid_price is not None:
                    st.metric("Mid Price", f"{mid_price:.2f}")
                else:
                    st.metric("Mid Price", "N/A")
            
            with metrics_col4:
                spread = summary['spread']
                if spread is not None:
                    st.metric("Spread", f"{spread:.3f}")
                else:
                    st.metric("Spread", "N/A")
        else:
            st.info("Simulation not started yet.")
    
    with status_col2:
        # Remove all auto-refresh functionality
        st.write("## Chart Controls")
        
        # Add a manual refresh explanation
        st.info("Use the 'Refresh Charts' button to update visualizations after running the simulation.")
        
        # Add option to limit data points for better performance
        max_points = st.slider("Max data points per chart", 100, 5000, 1000, 
                              help="Limit the number of data points shown in charts for better performance")
        
        if 'max_points' not in st.session_state:
            st.session_state.max_points = max_points
        else:
            st.session_state.max_points = max_points

    # Visualizations
    st.markdown("---")
    
    if st.session_state.simulator is not None:
        simulator = st.session_state.simulator
        
        # Force visualization even if there's a lot of data
        if 'force_viz' in st.session_state and st.session_state.force_viz:
            st.warning("Forcing visualization refresh - this may take a moment for large datasets")
            
            # Get the latest data directly from the simulator
            try:
                # Get current order book state
                bids_df, asks_df = simulator.order_book.get_order_book_as_dataframe()
                
                # Get history (limit to last 1000 ticks for performance)
                history_df = simulator.get_history_as_dataframe()
                if len(history_df) > 1000:
                    history_df = history_df.tail(1000)
                
                # Get trades (limit to last 500 for performance)
                trades_df = simulator.get_trade_log_as_dataframe()
                if len(trades_df) > 500:
                    trades_df = trades_df.tail(500)
                    
                # Explicitly create and display charts using the reduced datasets
                st.subheader("Order Book Depth (Current State)")
                depth_chart = create_depth_chart(bids_df, asks_df)
                st.plotly_chart(depth_chart, use_container_width=True)
                
                st.subheader("Recent Price Action (Last 1000 ticks)")
                price_chart = create_price_chart(history_df)
                st.plotly_chart(price_chart, use_container_width=True)
                
                if not trades_df.empty:
                    st.subheader("Recent Trades")
                    trades_chart = create_trades_chart(trades_df)
                    st.plotly_chart(trades_chart, use_container_width=True)
                
                st.success(f"Successfully refreshed visualizations at tick {simulator.tick_num}")
                
                # Reset the force_viz flag
                st.session_state.force_viz = False
                                
            except Exception as e:
                st.error(f"Error refreshing visualizations: {str(e)}")
                
            # Skip the regular visualization code
            st.stop()
            
        # Normal visualization code continues below for non-forced refreshes
        # Order book depth chart
        st.subheader("Order Book Depth")
        with st.expander("What is the Order Book Depth Chart?", expanded=False):
            st.markdown("""
            The Order Book Depth Chart shows the cumulative volume of buy (bid) and sell (ask) orders at each price level. 
            - **Green area (left)**: Bids (buy orders)
            - **Red area (right)**: Asks (sell orders)
            - The gap between the highest bid and lowest ask is the spread.
            - Steeper areas indicate more liquidity at those price levels.
            """)
            
        bids_df, asks_df = simulator.order_book.get_order_book_as_dataframe()
        depth_chart = create_depth_chart(bids_df, asks_df)
        st.plotly_chart(depth_chart, use_container_width=True)
        
        # Price history chart
        st.subheader("Price Chart")
        with st.expander("What is the Price Chart?", expanded=False):
            st.markdown("""
            The Price Chart shows the evolution of prices over time:
            - **Blue line**: Mid price (average of best bid and best ask)
            - **Green line**: Best bid price (highest buy order)
            - **Red line**: Best ask price (lowest sell order)
            - The gap between bid and ask represents the spread.
            """)
            
        history_df = simulator.get_history_as_dataframe()
        price_chart = create_price_chart(history_df)
        st.plotly_chart(price_chart, use_container_width=True)
        
        # Trades visualization
        st.subheader("Trade Activity")
        with st.expander("What is the Trade Activity Chart?", expanded=False):
            st.markdown("""
            The Trade Activity chart shows executed trades:
            - **Green triangles pointing up**: Buy trades (buyer was the aggressor)
            - **Red triangles pointing down**: Sell trades (seller was the aggressor)
            - The size of each marker represents the relative quantity of the trade.
            - Hover over points to see exact price and quantity information.
            """)
            
        trades_df = simulator.get_trade_log_as_dataframe()
        
        if not trades_df.empty:
            # Generate and display the trades chart
            trades_chart = create_trades_chart(trades_df)
            st.plotly_chart(trades_chart, use_container_width=True)
        else:
            st.info("No trades executed yet.")
        
        # Create two columns for remaining charts
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Spread chart
            st.subheader("Spread Over Time")
            with st.expander("What is the Spread Chart?", expanded=False):
                st.markdown("""
                The Spread Chart shows how the bid-ask spread changes over time:
                - Lower values indicate tighter spreads and more liquid markets.
                - Higher values indicate wider spreads and potentially less liquid markets.
                - Sudden spikes may indicate volatility or reduced liquidity.
                """)
                
            spread_chart = create_spread_chart(history_df)
            st.plotly_chart(spread_chart, use_container_width=True)
            
        with col_right:
            # Agent P&L comparison
            st.subheader("Agent P&L Comparison")
            with st.expander("What is the Agent P&L Chart?", expanded=False):
                st.markdown("""
                The Agent P&L chart shows the profit and loss of each agent over time:
                - Each line represents a different agent.
                - Upward trends indicate profitable strategies.
                - Market makers typically aim for steady growth with small profits.
                - Aggressive traders may show more volatile P&L patterns.
                """)
                
            agent_metrics = {
                agent_id: simulator.get_agent_metrics_as_dataframe(agent_id)
                for agent_id in simulator.agents
            }
            pnl_chart = create_agent_pnl_chart(agent_metrics, st.session_state.agent_names)
            st.plotly_chart(pnl_chart, use_container_width=True)
        
        # Volume heatmap
        st.subheader("Volume Distribution")
        with st.expander("What is the Volume Heatmap?", expanded=False):
            st.markdown("""
            The Volume Heatmap shows the distribution of trading volume across time and price levels:
            - Brighter/darker colors indicate higher/lower trading volumes.
            - Helps identify price levels with the most activity.
            - Shows how trading activity distributes across different price ranges over time.
            """)
            
        if not trades_df.empty and len(trades_df) > 3:
            volume_heatmap = create_volume_heatmap(trades_df)
            st.plotly_chart(volume_heatmap, use_container_width=True)
        else:
            st.info("Not enough trades for volume heatmap visualization.")
        
        # Trade log table
        st.subheader("Recent Trades")
        with st.expander("Trade Log Details", expanded=False):
            st.markdown("""
            The trade log shows details of each executed trade:
            - **Trade ID**: Unique identifier for the trade
            - **Timestamp**: When the trade occurred
            - **Price**: Execution price
            - **Quantity**: Number of units traded
            - **Buyer/Seller**: The agents involved in the trade
            - **Aggressor Side**: Which side initiated the trade (buy/sell)
            """)
            
        if not trades_df.empty:
            # Format and display the most recent trades (up to 10)
            display_df = trades_df.tail(10).copy()
            
            # Convert OrderSide enum objects to strings - now handled directly in order_book.py
            if 'aggressor_side' in display_df.columns:
                # Ensure the aggressor_side is a clean string value
                display_df['aggressor_side'] = display_df['aggressor_side'].astype(str)
                
                # If it's a string representation of an enum, clean it up
                if display_df['aggressor_side'].str.contains("OrderSide").any():
                    display_df['aggressor_side'] = display_df['aggressor_side'].str.extract(r"'(buy|sell)'", expand=False)
                
            # Double-check buyer_id and seller_id are different from each other
            invalid_trades = display_df['buyer_id'] == display_df['seller_id']
            if invalid_trades.any():
                st.warning(f"Found {invalid_trades.sum()} trades where buyer and seller are the same. These may be errors.")
                
            # Replace agent IDs with names
            display_df['buyer_name'] = display_df['buyer_id'].map(
                lambda x: st.session_state.agent_names.get(x, x[:8])
            )
            display_df['seller_name'] = display_df['seller_id'].map(
                lambda x: st.session_state.agent_names.get(x, x[:8])
            )
            
            # Select and format columns for display
            display_df = display_df[['trade_id', 'timestamp', 'price', 'quantity', 
                                    'buyer_name', 'seller_name', 'aggressor_side']]
            display_df = display_df.rename(columns={
                'buyer_name': 'Buyer',
                'seller_name': 'Seller',
                'trade_id': 'Trade ID',
                'timestamp': 'Time',
                'price': 'Price',
                'quantity': 'Qty',
                'aggressor_side': 'Aggressor'
            })
            
            st.dataframe(display_df.iloc[::-1], use_container_width=True)
        else:
            st.info("No trades executed yet.")
    else:
        st.info("Start the simulation to see visualizations.")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="background-color: {COLOR_MIDNIGHT_BLUE}; padding: 20px; border-radius: 10px; color: white;">
    <h3 style="color: {COLOR_DESERT_SUN} !important;">About This Simulator</h3>
    
    <p>This Order Book Simulator is an educational tool for understanding market microstructure mechanics.
    It simulates a central limit order book with various agent types and provides visualizations of market dynamics.</p>
    
    <h4 style="color: {COLOR_DESERT_SUN} !important;">Key Concepts:</h4>
    <ul>
    <li><strong style="color: {COLOR_BURNT_ORANGE}">Order Book</strong>: A record of all orders waiting to be executed</li>
    <li><strong style="color: {COLOR_BURNT_ORANGE}">Market Orders</strong>: Execute immediately at the best available price</li>
    <li><strong style="color: {COLOR_BURNT_ORANGE}">Limit Orders</strong>: Execute only at the specified price or better</li>
    <li><strong style="color: {COLOR_BURNT_ORANGE}">Spread</strong>: The difference between best bid and best ask prices</li>
    </ul>
    
    <h4 style="color: {COLOR_DESERT_SUN} !important;">Agent Types:</h4>
    <ul>
    <li><strong style="color: {COLOR_BURNT_ORANGE}">Market Makers</strong>: Provide liquidity by quoting on both sides</li>
    <li><strong style="color: {COLOR_BURNT_ORANGE}">Aggressive Traders</strong>: Take liquidity with market orders</li>
    <li><strong style="color: {COLOR_BURNT_ORANGE}">Noise Traders</strong>: Generate random orders</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()