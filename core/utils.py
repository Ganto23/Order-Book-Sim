"""
Utility functions for the OrderBookSim project.
"""

import time
import uuid
import numpy as np
from typing import Optional


def generate_order_id() -> str:
    """Generate a unique order ID."""
    return str(uuid.uuid4())


def get_timestamp() -> float:
    """Get current timestamp."""
    return time.time()


def round_to_tick(price: float, tick_size: float) -> float:
    """
    Round a price to the nearest tick size.
    
    Args:
        price: The price to round
        tick_size: Minimum price increment
        
    Returns:
        Price rounded to the nearest tick
    """
    return round(price / tick_size) * tick_size


def random_price_near(reference_price: float, spread_range: float, 
                     tick_size: float) -> float:
    """
    Generate a random price near a reference price.
    
    Args:
        reference_price: Base price
        spread_range: Range within which to generate a price
        tick_size: Minimum price increment
        
    Returns:
        Randomized price rounded to tick size
    """
    offset = np.random.uniform(-spread_range, spread_range)
    return round_to_tick(reference_price + offset, tick_size)


def format_price(price: Optional[float]) -> str:
    """Format a price for display."""
    if price is None:
        return "N/A"
    return f"{price:.2f}"


def calculate_vwap(prices, volumes):
    """
    Calculate the Volume-Weighted Average Price.
    
    Args:
        prices: List of prices
        volumes: List of volumes corresponding to prices
        
    Returns:
        VWAP value or None if no data
    """
    if not prices or not volumes or len(prices) != len(volumes):
        return None
        
    total_volume = sum(volumes)
    if total_volume == 0:
        return None
        
    weighted_sum = sum(p * v for p, v in zip(prices, volumes))
    return weighted_sum / total_volume


def export_to_csv(data, filepath: str) -> bool:
    """
    Export data to a CSV file.
    
    Args:
        data: Pandas DataFrame to export
        filepath: Path to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        data.to_csv(filepath, index=False)
        return True
    except Exception:
        return False