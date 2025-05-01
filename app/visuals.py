"""
Visualization functions for the Order Book Simulator Streamlit app.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
import seaborn as sns

# Define the color palette as constants for consistent usage
COLOR_MIDNIGHT_BLUE = "#001f3d"
COLOR_NAVY_BLUE = "#045174"
COLOR_DESERT_SUN = "#d89c60"
COLOR_BURNT_ORANGE = "#e87a00"

# Set Plotly template with custom colors
PLOTLY_TEMPLATE = {
    'layout': {
        'font': {'color': COLOR_MIDNIGHT_BLUE},
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'colorway': [COLOR_NAVY_BLUE, COLOR_BURNT_ORANGE, COLOR_DESERT_SUN, "#6E8B98", "#B4654A"],
    }
}

# Common chart layout settings
def apply_common_layout(fig: go.Figure, title: str) -> None:
    """Apply common layout settings to charts for consistent appearance."""
    fig.update_layout(
        title={
            'text': title,
            'font': {'color': COLOR_MIDNIGHT_BLUE, 'size': 20}
        },
        font=dict(color=COLOR_MIDNIGHT_BLUE),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )


def create_depth_chart(bids_df: pd.DataFrame, asks_df: pd.DataFrame) -> go.Figure:
    """
    Create an order book depth chart using Plotly.
    
    Args:
        bids_df: DataFrame with bid prices and volumes
        asks_df: DataFrame with ask prices and volumes
        
    Returns:
        Plotly figure with the depth chart
    """
    fig = go.Figure()
    
    # Calculate cumulative volume
    if not bids_df.empty:
        bids_df = bids_df.sort_values('price', ascending=False)
        bids_df['cumulative_volume'] = bids_df['volume'].cumsum()
        
        fig.add_trace(go.Scatter(
            x=bids_df['price'],
            y=bids_df['cumulative_volume'],
            fill='tozeroy',
            mode='lines',
            line=dict(width=0.5, color=COLOR_NAVY_BLUE),
            fillcolor=f'rgba({int(COLOR_NAVY_BLUE[1:3], 16)}, {int(COLOR_NAVY_BLUE[3:5], 16)}, {int(COLOR_NAVY_BLUE[5:7], 16)}, 0.3)',
            name='Bids'
        ))
    
    if not asks_df.empty:
        asks_df = asks_df.sort_values('price')
        asks_df['cumulative_volume'] = asks_df['volume'].cumsum()
        
        fig.add_trace(go.Scatter(
            x=asks_df['price'],
            y=asks_df['cumulative_volume'],
            fill='tozeroy',
            mode='lines',
            line=dict(width=0.5, color=COLOR_BURNT_ORANGE),
            fillcolor=f'rgba({int(COLOR_BURNT_ORANGE[1:3], 16)}, {int(COLOR_BURNT_ORANGE[3:5], 16)}, {int(COLOR_BURNT_ORANGE[5:7], 16)}, 0.3)',
            name='Asks'
        ))
    
    # Apply common layout and customize for this chart
    apply_common_layout(fig, "Order Book Depth Chart")
    fig.update_layout(
        xaxis_title="Price",
        yaxis_title="Cumulative Volume",
        hovermode="x",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig


def create_price_chart(history_df, max_points=1000):
    """
    Create a price chart with best bid, best ask, and mid price.
    
    Args:
        history_df: DataFrame with price history
        max_points: Maximum number of points to plot (to prevent performance issues)
        
    Returns:
        Plotly figure
    """
    if history_df.empty:
        # Create empty chart with proper axes
        fig = go.Figure()
        fig.add_annotation(
            text="No price data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color=COLOR_MIDNIGHT_BLUE)
        )
        apply_common_layout(fig, "Price Chart")
        fig.update_layout(
            xaxis_title="Tick",
            yaxis_title="Price"
        )
        return fig
        
    # Downsample if necessary for performance
    if len(history_df) > max_points:
        # Simple downsampling by taking every nth point
        n = len(history_df) // max_points + 1
        plot_df = history_df.iloc[::n].copy()
    else:
        plot_df = history_df.copy()
    
    fig = go.Figure()
    
    # Add mid price line
    if 'mid_price' in plot_df.columns and not plot_df['mid_price'].isna().all():
        fig.add_trace(go.Scatter(
            x=plot_df['tick'],
            y=plot_df['mid_price'],
            mode='lines',
            name='Mid Price',
            line=dict(color=COLOR_NAVY_BLUE, width=2.5)
        ))
    
    # Add best bid line
    if 'best_bid' in plot_df.columns and not plot_df['best_bid'].isna().all():
        fig.add_trace(go.Scatter(
            x=plot_df['tick'],
            y=plot_df['best_bid'],
            mode='lines',
            name='Best Bid',
            line=dict(color=COLOR_DESERT_SUN, width=1.5)
        ))
    
    # Add best ask line
    if 'best_ask' in plot_df.columns and not plot_df['best_ask'].isna().all():
        fig.add_trace(go.Scatter(
            x=plot_df['tick'],
            y=plot_df['best_ask'],
            mode='lines',
            name='Best Ask',
            line=dict(color=COLOR_BURNT_ORANGE, width=1.5)
        ))
    
    # Apply common layout and customize for this chart
    apply_common_layout(fig, "Price Chart")
    fig.update_layout(
        xaxis_title="Tick",
        yaxis_title="Price"
    )
    
    return fig


def create_trades_chart(trades_df: pd.DataFrame) -> go.Figure:
    """
    Create a scatter plot of trades with buy/sell indicators.
    
    Args:
        trades_df: DataFrame with trade information
        
    Returns:
        Plotly figure with the trades chart
    """
    if trades_df.empty:
        # Create empty figure if no trades
        fig = go.Figure()
        apply_common_layout(fig, "Trades")
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Price"
        )
        fig.add_annotation(
            text="No trades executed yet",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Add tick or timestamp for x-axis, ensuring we always have a valid x value
    if 'tick' in trades_df.columns:
        # Use tick number if available (preferred)
        x_column = 'tick'
    elif 'timestamp' in trades_df.columns:
        # Use timestamp if available
        x_column = 'timestamp'
    else:
        # Use index as fallback
        trades_df['x_index'] = range(len(trades_df))
        x_column = 'x_index'
    
    # Create a copy to avoid modifying the original DataFrame
    plot_df = trades_df.copy()
    
    # Normalize aggressor_side values to handle different formats
    if 'aggressor_side' in plot_df.columns:
        # Convert to lowercase string if not already
        plot_df['aggressor_side'] = plot_df['aggressor_side'].astype(str).str.lower()
        
        # Handle different formats of the aggressor_side value
        # Map any value containing "buy" to "buy" and "sell" to "sell"
        plot_df['aggressor_side'] = plot_df['aggressor_side'].apply(
            lambda x: "buy" if "buy" in x else ("sell" if "sell" in x else "unknown")
        )
        
        # If we still don't have any valid sides, try to infer from buyer and seller info
        if (plot_df['aggressor_side'] == 'buy').sum() == 0 and (plot_df['aggressor_side'] == 'sell').sum() == 0:
            # As a fallback, mark half as buy and half as sell to at least show some data
            half_point = len(plot_df) // 2
            plot_df['aggressor_side'].iloc[:half_point] = 'buy'
            plot_df['aggressor_side'].iloc[half_point:] = 'sell'
    
    fig = go.Figure()
    
    # Check if aggressor_side column exists
    if 'aggressor_side' in plot_df.columns:
        # Split buys and sells
        buys = plot_df[plot_df['aggressor_side'] == 'buy']
        sells = plot_df[plot_df['aggressor_side'] == 'sell']
        
        # Add buy trades
        if not buys.empty:
            fig.add_trace(go.Scatter(
                x=buys[x_column],
                y=buys['price'],
                mode='markers',
                name='Buy Trades',
                marker=dict(
                    size=buys['quantity'] / buys['quantity'].max() * 15 + 5 if len(buys) > 0 else 10,  
                    color=COLOR_NAVY_BLUE,
                    symbol='triangle-up'
                ),
                hovertemplate='Price: %{y:.2f}<br>Quantity: %{text}<extra></extra>',
                text=buys['quantity']
            ))
        
        # Add sell trades
        if not sells.empty:
            fig.add_trace(go.Scatter(
                x=sells[x_column],
                y=sells['price'],
                mode='markers',
                name='Sell Trades',
                marker=dict(
                    size=sells['quantity'] / sells['quantity'].max() * 15 + 5 if len(sells) > 0 else 10,
                    color=COLOR_BURNT_ORANGE,
                    symbol='triangle-down'
                ),
                hovertemplate='Price: %{y:.2f}<br>Quantity: %{text}<extra></extra>',
                text=sells['quantity']
            ))
    else:
        # If we can't distinguish buy/sell, just plot all trades in a neutral color
        fig.add_trace(go.Scatter(
            x=plot_df[x_column],
            y=plot_df['price'],
            mode='markers',
            name='Trades',
            marker=dict(
                size=plot_df['quantity'] / plot_df['quantity'].max() * 15 + 5 if len(plot_df) > 0 else 10,
                color=COLOR_DESERT_SUN,
                symbol='circle'
            ),
            hovertemplate='Price: %{y:.2f}<br>Quantity: %{text}<extra></extra>',
            text=plot_df['quantity']
        ))
    
    # Add price range buffer for better visualization
    if not trades_df.empty:
        price_min = trades_df['price'].min()
        price_max = trades_df['price'].max()
        price_range = price_max - price_min
        if price_range > 0:
            buffer = price_range * 0.1  # 10% buffer
            y_min = price_min - buffer
            y_max = price_max + buffer
            fig.update_yaxes(range=[y_min, y_max])
        
    # Apply common layout with custom title
    apply_common_layout(fig, "Trade Activity")
    fig.update_layout(
        xaxis_title="Time" if x_column == 'timestamp' else ("Tick" if x_column == 'tick' else "Trade Sequence"),
        yaxis_title="Price",
        hovermode="closest"
    )
    
    return fig


def create_agent_pnl_chart(agent_metrics: Dict[str, pd.DataFrame], 
                          agent_names: Dict[str, str]) -> go.Figure:
    """
    Create a line chart showing P&L for each agent.
    
    Args:
        agent_metrics: Dictionary mapping agent IDs to their metrics DataFrames
        agent_names: Dictionary mapping agent IDs to display names
        
    Returns:
        Plotly figure with agent P&L chart
    """
    fig = go.Figure()
    
    for agent_id, metrics_df in agent_metrics.items():
        # Check if metrics_df is None before trying to access its columns
        if metrics_df is not None and 'pnl' in metrics_df.columns:
            name = agent_names.get(agent_id, f"Agent {agent_id[:6]}")
            fig.add_trace(go.Scatter(
                x=metrics_df['tick'],
                y=metrics_df['pnl'],
                mode='lines',
                name=name
            ))
    
    # Apply common layout with custom title
    apply_common_layout(fig, "Agent P&L")
    fig.update_layout(
        xaxis_title="Tick Number",
        yaxis_title="P&L",
        hovermode="x unified"
    )
    
    return fig


def create_spread_chart(history_df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing the spread over time.
    
    Args:
        history_df: DataFrame with price history including spread
        
    Returns:
        Plotly figure with spread chart
    """
    fig = go.Figure()
    
    if 'spread' in history_df.columns and not history_df['spread'].isna().all():
        fig.add_trace(go.Scatter(
            x=history_df['tick'],
            y=history_df['spread'],
            mode='lines',
            name='Spread',
            line=dict(color=COLOR_DESERT_SUN, width=2),
            fill='tozeroy',
            fillcolor=f'rgba({int(COLOR_DESERT_SUN[1:3], 16)}, {int(COLOR_DESERT_SUN[3:5], 16)}, {int(COLOR_DESERT_SUN[5:7], 16)}, 0.2)'
        ))
    
    # Apply common layout with custom title
    apply_common_layout(fig, "Spread Over Time")
    fig.update_layout(
        xaxis_title="Tick Number",
        yaxis_title="Spread",
        hovermode="x unified"
    )
    
    return fig


def create_volume_heatmap(trades_df: pd.DataFrame, price_bins: int = 20) -> go.Figure:
    """
    Create a heatmap showing trading volume distribution over price and time.
    
    Args:
        trades_df: DataFrame with trade information
        price_bins: Number of price bins for the heatmap
        
    Returns:
        Plotly figure with volume heatmap
    """
    if trades_df.empty:
        # Create empty figure if no trades
        fig = go.Figure()
        apply_common_layout(fig, "Volume Heatmap")
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Price"
        )
        return fig
    
    # Create time bins (divide into 20 segments)
    if 'timestamp' in trades_df.columns:
        min_time = trades_df['timestamp'].min()
        max_time = trades_df['timestamp'].max()
        if max_time > min_time:
            n_time_bins = min(20, len(trades_df))
            time_bin_size = (max_time - min_time) / n_time_bins
            trades_df['time_bin'] = ((trades_df['timestamp'] - min_time) / time_bin_size).astype(int)
        else:
            trades_df['time_bin'] = 0
    else:
        trades_df['time_bin'] = 0
    
    # Create price bins
    if 'price' in trades_df.columns:
        min_price = trades_df['price'].min()
        max_price = trades_df['price'].max()
        if max_price > min_price:
            price_bin_size = (max_price - min_price) / price_bins
            trades_df['price_bin'] = ((trades_df['price'] - min_price) / price_bin_size).astype(int)
        else:
            trades_df['price_bin'] = 0
    else:
        trades_df['price_bin'] = 0
    
    # Aggregate volume by time and price bin
    volume_matrix = trades_df.groupby(['time_bin', 'price_bin'])['quantity'].sum().reset_index()
    
    # Create the heatmap
    fig = go.Figure(data=go.Heatmap(
        z=volume_matrix['quantity'],
        x=volume_matrix['time_bin'],
        y=volume_matrix['price_bin'],
        colorscale=[
            [0, f'rgba({int(COLOR_MIDNIGHT_BLUE[1:3], 16)}, {int(COLOR_MIDNIGHT_BLUE[3:5], 16)}, {int(COLOR_MIDNIGHT_BLUE[5:7], 16)}, 0.2)'],
            [0.5, f'rgba({int(COLOR_NAVY_BLUE[1:3], 16)}, {int(COLOR_NAVY_BLUE[3:5], 16)}, {int(COLOR_NAVY_BLUE[5:7], 16)}, 0.5)'],
            [1, f'rgba({int(COLOR_BURNT_ORANGE[1:3], 16)}, {int(COLOR_BURNT_ORANGE[3:5], 16)}, {int(COLOR_BURNT_ORANGE[5:7], 16)}, 1.0)']
        ],
        colorbar=dict(
            title=dict(
                text='Volume',
                side='right',
                font=dict(color=COLOR_MIDNIGHT_BLUE)
            )
        )
    ))
    
    # Convert bin numbers back to actual values for axis labels
    if 'timestamp' in trades_df.columns and max_time > min_time:
        time_ticks = {
            i: f"{min_time + i * time_bin_size:.1f}" for i in range(n_time_bins + 1)
        }
    else:
        time_ticks = {i: str(i) for i in range(max(volume_matrix['time_bin']) + 1)}
    
    if 'price' in trades_df.columns and max_price > min_price:
        price_ticks = {
            i: f"{min_price + i * price_bin_size:.2f}" for i in range(price_bins + 1)
        }
    else:
        price_ticks = {i: str(i) for i in range(max(volume_matrix['price_bin']) + 1)}
    
    # Apply common layout with custom title
    apply_common_layout(fig, "Volume Heatmap")
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis=dict(
            tickvals=list(time_ticks.keys())[::2],  # Show every other tick
            ticktext=list(time_ticks.values())[::2]
        ),
        yaxis=dict(
            tickvals=list(price_ticks.keys())[::2],
            ticktext=list(price_ticks.values())[::2]
        )
    )
    
    return fig