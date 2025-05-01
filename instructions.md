# 🧠 Prompt: Build Me an Order Book Simulator with Streamlit Frontend

I want to build an educational, interactive, and realistic **limit order book (LOB) simulator** using Python. This project should simulate market microstructure mechanics with multiple trader types and provide a clean **Streamlit frontend** for real-time visualization.

---

## 🎯 Objectives

Build a complete simulator that replicates a central limit order book, including:

### 🧩 Core Functionality
1. **Order matching engine** for:
   - Limit orders (buy/sell)
   - Market orders
   - Order cancellations
   - Partial fills and time-priority queueing

2. **Trader agent logic**:
   - Market makers (quote both sides, update quotes)
   - Aggressive traders (execute via market orders)
   - Noise/random traders (random behavior)
   - Optional: Add iceberg or hidden orders

3. **Book state management**:
   - Track full order book at every time step
   - Log trades with price, volume, aggressor
   - Maintain top-of-book quotes, mid-price, spread, and book depth

4. **Simulation loop**:
   - Discrete time simulation
   - Agents take actions each tick
   - Track all events and state updates

---

## 🖥️ Streamlit Frontend Features

Build a simple and intuitive **Streamlit dashboard** that allows users to:

- 🔧 Configure simulation parameters:
  - Number of agents
  - Tick size
  - Order frequency
  - Simulation length

- 🎮 Start and pause the simulation

- 📈 View live charts:
  - Depth chart of the order book
  - Trade log (scrolling table)
  - Time series of bid/ask, spread, mid-price
  - Volume heatmap over price levels

- 📤 Export trade logs and order book snapshots (CSV)

Optional: Include sidebar tooltips explaining microstructure concepts.

---

## 🧰 Required Features

- Modular Python architecture:
  - `order_book.py`: Matching logic and LOB structure
  - `agents/`: Contains various trader classes
  - `simulator.py`: Manages ticks and agent actions
  - `streamlit_app.py`: Dashboard entry point
  - `visuals.py`: Plotting functions for Streamlit

- Use:
  - `pandas`, `numpy`, `matplotlib`, `plotly`, `seaborn`, `streamlit`

- Include:
  - `.env` for settings (optional)
  - `README.md` with usage instructions and theory
  - `requirements.txt` with all needed packages
  - `notebooks/` folder with a non-UI version for quick testing

---

## 📁 Suggested Project Structure

```plaintext
order-book-simulator/
│
├── core/
│   ├── order_book.py          # Matching engine and book structure
│   └── utils.py               # Timestamps, order ID generators, etc.
│
├── agents/
│   ├── base_agent.py
│   ├── market_maker.py
│   ├── aggressive_trader.py
│   └── noise_trader.py
│
├── sim/
│   ├── simulator.py           # Event loop
│   └── config.py              # Parameters for agents, ticks, etc.
│
├── app/
│   ├── streamlit_app.py       # Streamlit interface
│   └── visuals.py             # Live plotting functions for UI
│
├── notebooks/
│   └── demo_simulation.ipynb
│
├── data/                      # Trade logs, book states (CSV)
├── README.md
├── requirements.txt
└── .env
