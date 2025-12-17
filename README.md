# GEMSCAP - Real-Time Quantitative Trading Analytics Platform

> **Statistical Arbitrage & Mean Reversion Trading System**  
> Full-stack fintech application for real-time crypto market analysis, spread trading, and correlation monitoring with live Binance data streaming.

![image alt](https://github.com/mayur-borole/Gemscap_Project/blob/aa663df572cb5e7273a2b6236f1965cd474c46ca/Artitecture%20of%20project.png)

## Architectural Principles

**Clear Separation of Concerns**  
Ingestion, resampling, analytics, and presentation are isolated into separate modules with well-defined interfaces.

**Frontend-Backend Decoupling**  
The frontend interacts only through WebSocket and REST endpoints. It does not directly access raw data sources or internal state.

**Pluggable Components**  
Data providers and storage mechanisms can be replaced with minimal changes. The system does not depend on specific exchange APIs beyond the ingestion layer.

**Minimal Necessary Complexity**  
No distributed message queues, microservices orchestration, or complex infrastructure were introduced. The architecture reflects the actual requirements of the system: real-time data processing and research-oriented presentation.

## Methodology

The project was built incrementally, ensuring each component worked correctly before moving to the next.

**Step 1: Live Market Data Streaming**  
First, a WebSocket connection to Binance Futures was established to stream tick data for multiple assets (BTC, ETH, SOL). At this stage, the system only focused on reliably receiving and buffering data without performing analytics. Keeping ingestion lightweight ensures minimal delay and no dropped ticks when the stream is active.

**Step 2: Data Storage and Time Alignment**  
Incoming raw tick data is buffered in memory with a capacity limit. For analysis, this raw data is resampled into fixed time intervals (1s, 1m, 5m, 15m, 1h) and aligned across assets. All subsequent calculations are performed on this resampled, time-aligned data to ensure statistical metrics remain stable and comparable across different timeframes.

**Step 3: Core Analytics Implementation**  
Once the data pipeline was stable, core analytics were implemented using standard quantitative techniques:
- Hedge ratio estimation using Ordinary Least Squares (OLS) regression
- Spread computation between asset pairs
- Rolling z-score calculation to measure deviation from the mean
- Rolling correlation to assess relationship strength
- Multiple regression methods (OLS, TLS, RANSAC, Huber) for robustness testing

All analytics are implemented as stateless functions that operate on resampled data, making them easy to test and reuse.

**Step 4: Interpretation and Alerting**  
Rather than displaying raw numbers alone, an interpretation layer was added. The system explains what current signals indicate and highlights conditions that deserve attention:
- Z-score extremes (potential mean reversion opportunities)
- Correlation breakdown (relationship weakening)
- Volatility spikes (possible regime change)
- Alert cooldown mechanisms prevent notification spam

These alerts are informational and designed to support research monitoring, not automated decision-making.

**Step 5: Interactive Dashboard**  
Everything is presented through an interactive web dashboard built with React. The interface is separated into logical sections:
- Control panel for selecting assets, timeframes, and thresholds
- Price charts showing multi-asset comparisons with dual y-axes
- Spread and z-score visualization with threshold bands
- Correlation charts and summary statistics
- Alert panel displaying active notifications
- Data export functionality for further analysis

Changing inputs like asset pairs or rolling windows updates analytics in real time, making the dashboard suitable for exploratory research.

## Technology Stack

**Language**  
Python 3.10+  
Chosen for its strong ecosystem in data processing, statistics, and rapid prototyping.

**Market Data Ingestion**  
WebSocket connection to Binance Futures  
`asyncio`, `websockets`  
Chosen to support:
- Low-latency streaming data
- Event-driven ingestion architecture
- Non-blocking concurrent operations

**Analytics**  
`pandas`, `numpy` for data manipulation  
`scikit-learn` for regression methods  
`statsmodels` for statistical tests  
Chosen to implement:
- Regression-based hedge ratios
- Rolling statistics (mean, std, correlation)
- Multiple regression techniques for robustness

All analytics are implemented as stateless functions for clarity and reuse.

**Backend Framework**  
FastAPI with Uvicorn  
Chosen because:
- Native async support for WebSocket broadcasting
- Automatic API documentation
- Type validation with Pydantic
- Lightweight and fast for real-time applications

**Frontend**  
React 18 with TypeScript  
Vite for build tooling  
Recharts for visualization  
Chosen because:
- Component-based architecture matches the modular design
- TypeScript provides type safety for real-time data handling
- Recharts offers interactive, research-grade visualizations
- Vite enables fast development iteration

The frontend is intentionally research-oriented, not designed as a production trading interface.

## Analytics Implemented

**Hedge Ratio (OLS Regression)**  
Estimates the linear relationship between two assets using ordinary least squares, a standard approach in statistical arbitrage. The hedge ratio determines the relative position sizes for spread construction.

**Spread**  
Computed as the residual between hedged assets: `Spread = Asset1 - (HedgeRatio × Asset2)`. This represents deviations from the historical relationship.

**Rolling Z-Score**  
Measures how many standard deviations the spread is from its recent mean over a configurable window. Used to identify statistically significant deviations:
- Z-score > +2.0: Spread overextended (potential reversion)
- Z-score < -2.0: Spread underextended (potential reversion)

**Rolling Correlation**  
Evaluates the stability of the asset relationship over time. Low correlation indicates the pair relationship may be breaking down, reducing signal reliability.

**Multiple Regression Methods**  
In addition to OLS, the system supports:
- Total Least Squares (TLS): Accounts for errors in both variables
- RANSAC: Robust to outliers
- Huber Regression: Reduces influence of outliers

These alternatives provide diagnostic tools to assess model robustness.

## Alerting & Interpretation

**Alerts Implemented**  
- Z-score extremes (>±2.0σ by default, configurable)
- Correlation breakdown (<0.5 by default)
- Spread volatility spikes (unusual standard deviation)
- Alert cooldown (60 seconds) to prevent spam

**Interpretation Layer**  
Numerical signals are accompanied by:
- Qualitative explanations of what the signal implies
- Confidence assessment based on correlation strength
- Guidance on what conditions to monitor next

This avoids prescriptive trading advice while improving interpretability for researchers.

## Frontend Design Philosophy

The dashboard is designed as an internal research tool:
- Split views for prices, signals, and diagnostics
- Compact summary cards for quick context
- Minimal styling focused on clarity and information density
- Interactive controls for exploratory analysis

The goal is to reflect how quantitative analytics are consumed in practice, not to replicate retail trading platforms.

## Handling of Data Limitations

Rolling metrics require sufficient historical data. Until enough data is available:
- Some calculated fields may show NaN values
- The UI communicates these conditions explicitly
- The system gracefully handles incomplete data without crashing

As more data accumulates, metrics stabilize and become reliable.

## Development Approach: AI-Assisted Workflow

This project leveraged AI tools strategically to accelerate development while maintaining code quality:

**Time-Saving Applications:**
- **Architecture Design**: Used GPT to validate architectural decisions and identify potential bottlenecks before implementation
- **Boilerplate Generation**: Generated repetitive code structures (API schemas, WebSocket handlers, React components) in seconds rather than hours
- **Debugging Assistance**: Quickly identified root causes of async/WebSocket connection issues and statistical calculation errors
- **Documentation**: Automated generation of docstrings, type hints, and inline comments for better code maintainability
- **Code Review**: Received instant feedback on edge cases, error handling, and performance optimizations

**Key Productivity Gains:**
- Reduced initial setup time by ~60% (FastAPI + React scaffolding, dependency configuration)
- Faster iteration on complex statistical functions (z-score, correlation, regression models)
- Immediate answers to library-specific questions (pandas operations, Recharts configurations)
- Parallel development of frontend and backend without context-switching delays

**Smart Usage Pattern:**
Rather than blindly accepting AI-generated code, I used it as a collaborative tool: AI handled repetitive patterns while I focused on domain logic, data flow architecture, and business requirements. This hybrid approach delivered professional-grade code in a fraction of typical development time.

## Running the Project

**Prerequisites**
- Python 3.10+
- Node.js 18+ or Bun
- Windows, macOS, or Linux

**Backend Setup**
```bash
cd BackEnd
python -m venv venv

# Activate virtual environment
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
python run.py
```

The backend will start on `http://localhost:8000`. You should see log messages indicating successful connection to Binance WebSocket.

**Frontend Setup**
```bash
cd FrontEnd
npm install
npm run dev
```

The frontend will start on `http://localhost:8082`. Open this URL in your browser to access the dashboard.

**What You Should See**
- Real-time price updates for BTC, ETH, SOL
- Spread and z-score charts updating continuously
- Correlation metrics
- Alert notifications when thresholds are breached

## Key Files

**Backend**
- [BackEnd/app/main.py](BackEnd/app/main.py) - FastAPI application and REST endpoints
- [BackEnd/app/binance_client.py](BackEnd/app/binance_client.py) - WebSocket client for market data
- [BackEnd/app/ingestion.py](BackEnd/app/ingestion.py) - Tick data buffering
- [BackEnd/app/resampling.py](BackEnd/app/resampling.py) - OHLCV candle aggregation
- [BackEnd/app/analytics.py](BackEnd/app/analytics.py) - Statistical analysis functions
- [BackEnd/app/alerts.py](BackEnd/app/alerts.py) - Alert evaluation logic
- [BackEnd/app/websocket_manager.py](BackEnd/app/websocket_manager.py) - WebSocket broadcast manager

**Frontend**
- [FrontEnd/src/pages/Index.tsx](FrontEnd/src/pages/Index.tsx) - Main dashboard
- [FrontEnd/src/components/dashboard/ControlPanel.tsx](FrontEnd/src/components/dashboard/ControlPanel.tsx) - Settings controls
- [FrontEnd/src/components/dashboard/PriceChart.tsx](FrontEnd/src/components/dashboard/PriceChart.tsx) - Price visualization
- [FrontEnd/src/components/dashboard/SpreadZScoreChart.tsx](FrontEnd/src/components/dashboard/SpreadZScoreChart.tsx) - Statistical charts
- [FrontEnd/src/components/dashboard/AlertsPanel.tsx](FrontEnd/src/components/dashboard/AlertsPanel.tsx) - Alert display
- [FrontEnd/src/services/api.ts](FrontEnd/src/services/api.ts) - WebSocket and REST client
