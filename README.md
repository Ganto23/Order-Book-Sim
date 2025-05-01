# Order Book Simulator

An interactive limit order book simulator with a Streamlit frontend for education and exploration of market microstructure mechanics.

## 📊 Project Overview

This Order Book Simulator provides a realistic simulation of a central limit order book with multiple trader types. It's designed as an educational tool to understand:

- How limit order books work
- Price formation and market dynamics
- Trading agent behavior and strategies
- Market microstructure effects

## ✨ Features

- **Realistic Order Book Implementation**
  - Limit and market order support
  - Price-time priority matching
  - Order cancellations
  - Partial fills

- **Diverse Trading Agents**
  - Market Makers - quote on both sides with inventory management
  - Aggressive Traders - take liquidity with market orders
  - Noise Traders - random order placement and cancellations

- **Interactive Streamlit Interface**
  - Real-time visualizations
  - Configurable simulation parameters
  - Visualizations of order book, trades, and market metrics
  - Data export capabilities

## 🚀 Getting Started

### Prerequisites

- Python 3.8+ 
- Required packages (install via `requirements.txt`)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/order-book-simulator.git
cd order-book-simulator
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Simulator

1. Launch the Streamlit app:
```bash
streamlit run app/streamlit_app.py
```

2. Open your web browser to the URL displayed in the terminal (typically http://localhost:8501)

## 📖 Project Structure

```
order-book-simulator/
│
├── core/
│   ├── order_book.py          # Matching engine and book structure
│   └── utils.py               # Helper utilities
│
├── agents/
│   ├── base_agent.py          # Base agent class
│   ├── market_maker.py        # Market making strategy
│   ├── aggressive_trader.py   # Liquidity taking strategy
│   └── noise_trader.py        # Random trading strategy
│
├── sim/
│   ├── simulator.py           # Simulation loop
│   └── config.py              # Configuration management
│
├── app/
│   ├── streamlit_app.py       # Streamlit interface
│   └── visuals.py             # Visualization functions
│
├── notebooks/
│   └── demo_simulation.ipynb  # Example notebook
│
├── data/                      # Directory for output data
├── README.md
└── requirements.txt
```

## 📚 Market Microstructure Concepts

### Order Types

- **Limit Orders**: Orders with a specified price that may not execute immediately
- **Market Orders**: Orders that execute immediately at the best available price

### Key Terms

- **Bid**: Order to buy at a specified price
- **Ask/Offer**: Order to sell at a specified price
- **Spread**: Difference between best bid and best ask
- **Mid-Price**: Average of best bid and best ask
- **Market Depth**: Volume of orders at each price level
- **Liquidity**: Ease of executing trades without significant price impact

## 🤖 Agent Types

### Market Makers

Market makers provide liquidity by placing limit orders on both sides of the book. They aim to earn the spread while managing inventory risk. Key parameters:

- Quote spread: Width between bid and ask quotes
- Inventory skew: Adjustment of quotes based on current position
- Quote size: Volume quoted on each side

### Aggressive Traders

Aggressive traders take liquidity by executing market orders. They may have a target position or direction. Key parameters:

- Order rate: Frequency of order submission
- Position influence: How current position affects trading direction
- Order size: Typical trade size

### Noise Traders

Noise traders submit random orders with no particular strategy, simulating retail flow or undirected trading. Key parameters:

- Limit vs. market order probability
- Price range for limit orders
- Cancellation rate

## 📊 Visualizations

The simulator provides several real-time visualizations:

1. **Order Book Depth Chart**: Shows cumulative volume at each price level
2. **Price Chart**: Displays mid price, best bid, and best ask over time
3. **Trade Chart**: Shows executed trades with buy/sell indicators
4. **Spread Chart**: Tracks the bid-ask spread over time
5. **Agent P&L**: Compares the performance of different agents
6. **Volume Heatmap**: Shows distribution of volume across price and time

## 🔧 Configuration

The simulator can be configured through the Streamlit interface or by modifying `config.py`. Key parameters include:

- Market settings (tick size, initial price)
- Agent counts and parameters
- Simulation length and speed
- Visualization preferences
