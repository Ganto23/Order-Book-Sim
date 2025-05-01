"""
Configuration module for Order Book Simulator.
Defines default simulation settings and agent parameters.
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path


@dataclass
class MarketMakerConfig:
    """Configuration for market maker agents."""
    count: int = 2
    quote_spread: float = 0.05
    quote_volume: int = 10
    max_position: int = 100
    inventory_skew_factor: float = 0.01
    skew_quotes: bool = True


@dataclass
class AggressiveTraderConfig:
    """Configuration for aggressive trader agents."""
    count: int = 3
    order_rate: float = 0.2
    trade_size_min: int = 1
    trade_size_max: int = 20
    max_position: int = 100
    position_influence: float = 0.5


@dataclass
class NoiseTraderConfig:
    """Configuration for noise trader agents."""
    count: int = 5
    order_rate: float = 0.1
    limit_order_prob: float = 0.7
    price_range_factor: float = 0.02
    cancel_rate: float = 0.2
    size_min: int = 1
    size_max: int = 10


@dataclass
class SimulationConfig:
    """Main configuration for the simulation."""
    # Market settings
    tick_size: float = 0.01
    initial_price: float = 100.0
    
    # Simulation settings
    max_ticks: int = 1000
    step_delay: float = 0.05  # seconds between ticks when running in realtime
    log_trades: bool = True
    
    # Agent configurations
    market_makers: MarketMakerConfig = field(default_factory=MarketMakerConfig)
    aggressive_traders: AggressiveTraderConfig = field(default_factory=AggressiveTraderConfig)
    noise_traders: NoiseTraderConfig = field(default_factory=NoiseTraderConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)
    
    def save(self, filepath: str) -> bool:
        """
        Save configuration to JSON file.
        
        Args:
            filepath: Path to save the configuration file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    @classmethod
    def load(cls, filepath: str) -> Optional['SimulationConfig']:
        """
        Load configuration from JSON file.
        
        Args:
            filepath: Path to the configuration file
            
        Returns:
            Loaded configuration or None if failed
        """
        if not os.path.exists(filepath):
            return None
            
        try:
            with open(filepath, 'r') as f:
                config_dict = json.load(f)
            
            # Create nested objects
            if 'market_makers' in config_dict:
                config_dict['market_makers'] = MarketMakerConfig(**config_dict['market_makers'])
            if 'aggressive_traders' in config_dict:
                config_dict['aggressive_traders'] = AggressiveTraderConfig(**config_dict['aggressive_traders'])
            if 'noise_traders' in config_dict:
                config_dict['noise_traders'] = NoiseTraderConfig(**config_dict['noise_traders'])
                
            return cls(**config_dict)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None
            

def get_default_config() -> SimulationConfig:
    """Get default simulation configuration."""
    return SimulationConfig()


def get_demo_config() -> SimulationConfig:
    """Get a configuration suitable for demonstration."""
    config = SimulationConfig()
    
    # Faster updates for demo
    config.step_delay = 0.1
    config.max_ticks = 500
    
    # Configure agents for an active market
    config.market_makers.count = 3
    config.market_makers.quote_spread = 0.03
    config.market_makers.quote_volume = 15
    
    config.aggressive_traders.count = 4
    config.aggressive_traders.order_rate = 0.15
    
    config.noise_traders.count = 8
    config.noise_traders.order_rate = 0.12
    
    return config


def get_high_volatility_config() -> SimulationConfig:
    """Get configuration for a high volatility market."""
    config = SimulationConfig()
    
    # Configure agents for high volatility
    config.market_makers.count = 2
    config.market_makers.quote_spread = 0.08  # Wider spreads
    config.market_makers.inventory_skew_factor = 0.02  # More skew
    
    config.aggressive_traders.count = 6  # More aggressive traders
    config.aggressive_traders.order_rate = 0.3  # More frequent orders
    config.aggressive_traders.trade_size_max = 30  # Larger orders
    
    config.noise_traders.count = 10  # More noise
    config.noise_traders.price_range_factor = 0.04  # Wider price range
    
    return config


def get_low_liquidity_config() -> SimulationConfig:
    """Get configuration for a low liquidity market."""
    config = SimulationConfig()
    
    # Configure agents for low liquidity
    config.market_makers.count = 1  # Fewer market makers
    config.market_makers.quote_spread = 0.1  # Wider spreads
    config.market_makers.quote_volume = 5  # Less volume
    
    config.aggressive_traders.count = 2  # Fewer aggressive traders
    config.aggressive_traders.order_rate = 0.1  # Less frequent orders
    
    config.noise_traders.count = 3  # Less noise
    config.noise_traders.order_rate = 0.05  # Very infrequent orders
    
    return config