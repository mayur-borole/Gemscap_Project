"""
Test Analytics Engine - Core Quantitative Logic
Tests: Hedge Ratio, Spread, Z-Score, Correlation, ADF Test
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.binance_client import BinanceClient
from app.ingestion import get_ingestion_engine
from app.resampling import get_resampling_engine
from app.analytics import SpreadAnalyzer, CorrelationAnalyzer, StationarityTester


async def main():
    """Test all analytics functions."""
    print("\n" + "="*70)
    print("  🧮 ANALYTICS ENGINE TEST - Core Quantitative Logic")
    print("="*70)
    print("  Collecting 120 seconds (2 min) of live data for analysis...")
    print("  Using 1-second bars for faster data accumulation...")
    print("="*70 + "\n")
    
    # Initialize components
    ingestion = get_ingestion_engine()
    resampling = get_resampling_engine()
    client = BinanceClient(symbols=["BTCUSDT", "ETHUSDT"])
    
    # Connect pipeline
    async def handle_tick(tick):
        await ingestion.ingest_tick(tick)
        ticks = await ingestion.get_tick_history(tick.symbol, n=1000)
        await resampling.process_ticks(ticks, tick.symbol)
    
    client.subscribe_to_ticks(lambda tick: asyncio.create_task(handle_tick(tick)))
    
    # Start client
    client_task = asyncio.create_task(client.start())
    
    try:
        # Collect for 120 seconds (2 minutes) to get sufficient 1s bars
        print("  ⏳ Collecting data (this will take 2 minutes)...\n")
        await asyncio.sleep(120)
        
        # Stop client
        await client.stop()
        client_task.cancel()
        
        print("\n✓ Collection complete! Running analytics...\n")
        
        # Get 1-second bars for analysis (more bars = better analytics)
        btc_bars = await resampling.get_bars("BTCUSDT", "1s", n=100)
        eth_bars = await resampling.get_bars("ETHUSDT", "1s", n=100)
        
        if not btc_bars or not eth_bars:
            print("❌ Insufficient bar data collected")
            return
        
        # Align bars by timestamp (critical for OLS regression)
        btc_dict = {bar.timestamp: bar.close for bar in btc_bars}
        eth_dict = {bar.timestamp: bar.close for bar in eth_bars}
        
        # Find common timestamps
        common_timestamps = sorted(set(btc_dict.keys()) & set(eth_dict.keys()))
        
        # Extract aligned prices
        btc_prices = [btc_dict[ts] for ts in common_timestamps]
        eth_prices = [eth_dict[ts] for ts in common_timestamps]
        
        print(f"  Analyzing {len(btc_prices)} aligned price pairs (from {len(btc_bars)} BTC & {len(eth_bars)} ETH bars)\n")
        
        # Data sufficiency check
        MIN_BARS_REQUIRED = 30  # Minimum for reliable analytics
        if len(btc_bars) < MIN_BARS_REQUIRED or len(eth_bars) < MIN_BARS_REQUIRED:
            print("="*70)
            print("  ⚠️  DATA SUFFICIENCY WARNING")
            print("="*70)
            print(f"""
  Insufficient data for reliable analytics:
    • Minimum required: {MIN_BARS_REQUIRED} bars per symbol
    • BTC collected: {len(btc_bars)} bars
    • ETH collected: {len(eth_bars)} bars
  
  Why this matters:
    • OLS regression needs 20-50 points for stability
    • Z-score requires sufficient variance
    • ADF test needs 12+ points minimum
    • Correlation is unreliable with <30 points
  
  Solutions:
    1. Run test for longer (2-3 minutes)
    2. Use shorter resampling interval (1s instead of 1m)
    3. Check WebSocket connection stability
            """)
            print("="*70)
            print("  ⏹️  Test stopped due to insufficient data")
            print("="*70)
            return
        
        # Initialize variables for summary
        hedge_ratio = 0.0
        latest_spread = 0.0
        latest_time = "unknown"
        zscore = 0.0
        correlation = 0.0
        adf_result = {"p_value": 1.0, "stationary": False, "interpretation": "No data"}
        
        # ====================================================================
        # 1️⃣ HEDGE RATIO (OLS)
        # ====================================================================
        print("="*70)
        print("  1️⃣  HEDGE RATIO via OLS Regression")
        print("="*70)
        print("""
  Formula: BTC_price = \u03b1 + \u03b2 * ETH_price + \u03b5
  
  Where \u03b2 (hedge_ratio) minimizes: \u03a3(BTC_i - \u03b1 - \u03b2*ETH_i)\u00b2
        """)
        
        analyzer = SpreadAnalyzer(window=20)
        hedge_ratio = analyzer.compute_hedge_ratio(btc_prices, eth_prices)
        
        result_1 = {
            "hedge_ratio": round(hedge_ratio, 4)
        }
        
        print("  Output:")
        print("  " + json.dumps(result_1, indent=2))
        print(f"\n  Interpretation: 1 BTC = {hedge_ratio:.4f} ETH in linear relationship")
        
        # ====================================================================
        # 2️⃣ SPREAD
        # ====================================================================
        print("\n" + "="*70)
        print("  2️⃣  SPREAD Computation")
        print("="*70)
        print("""
  Formula: spread(t) = BTC_price(t) - hedge_ratio * ETH_price(t)
        """)
        
        spread_series, _ = analyzer.compute_spread(btc_prices, eth_prices)
        
        if spread_series:
            latest_spread = spread_series[-1]
            latest_time = btc_bars[-1].timestamp.split('T')[1] if 'T' in btc_bars[-1].timestamp else "unknown"
            
            result_2 = {
                "timestamp": latest_time,
                "spread": round(latest_spread, 2)
            }
            
            print("  Output:")
            print("  " + json.dumps(result_2, indent=2))
            print(f"\n  Recent spread values: {[round(s, 2) for s in spread_series[-5:]]}")
        
        # ====================================================================
        # 3️⃣ Z-SCORE
        # ====================================================================
        print("\n" + "="*70)
        print("  3️⃣  Z-SCORE (Mean Reversion Signal)")
        print("="*70)
        print("""
  Formula: z = (spread_current - \u03bc) / \u03c3
  
  Where:
    \u03bc = mean of spread over rolling window
    \u03c3 = standard deviation
  
  Trading signals:
    z > +2: Overvalued (SHORT signal)
    z < -2: Undervalued (LONG signal)
    -2 < z < +2: Neutral
        """)
        
        if spread_series:
            zscore = analyzer.compute_zscore(spread_series)
            
            if zscore is not None:
                result_3 = {
                    "timestamp": latest_time,
                    "z_score": round(zscore, 2)
                }
                
                print("  Output:")
                print("  " + json.dumps(result_3, indent=2))
                
                # Interpretation
                if zscore > 2:
                    signal = "🔴 SHORT Signal (spread overvalued)"
                elif zscore < -2:
                    signal = "🟢 LONG Signal (spread undervalued)"
                else:
                    signal = "⚪ NEUTRAL (spread near mean)"
                
                print(f"\n  {signal}")
        
        # ====================================================================
        # 4️⃣ ROLLING CORRELATION
        # ====================================================================
        print("\n" + "="*70)
        print("  4️⃣  ROLLING CORRELATION")
        print("="*70)
        print("""
  Formula: \u03c1(X,Y) = Cov(X,Y) / (\u03c3_X * \u03c3_Y)
  
  Range: -1 \u2264 \u03c1 \u2264 +1
    \u03c1 = +1: Perfect positive correlation
    \u03c1 = 0: No linear correlation
    \u03c1 = -1: Perfect negative correlation
        """)
        
        corr_analyzer = CorrelationAnalyzer(window=30)
        correlation = corr_analyzer.compute_correlation(btc_prices, eth_prices)
        
        if correlation is not None:
            result_4 = {
                "timestamp": latest_time,
                "correlation": round(correlation, 4)
            }
            
            print("  Output:")
            print("  " + json.dumps(result_4, indent=2))
            
            # Interpretation
            if correlation > 0.8:
                interp = "Strong positive correlation (good for pairs trading)"
            elif correlation > 0.5:
                interp = "Moderate positive correlation"
            else:
                interp = "Weak correlation (risky for pairs trading)"
            
            print(f"\n  {interp}")
        
        # ====================================================================
        # 5️⃣ AUGMENTED DICKEY-FULLER TEST
        # ====================================================================
        print("\n" + "="*70)
        print("  5️⃣  AUGMENTED DICKEY-FULLER TEST (Stationarity)")
        print("="*70)
        print("""
  Tests null hypothesis: H0 = Time series has unit root (non-stationary)
  
  ADF equation:
    \u0394y_t = \u03b1 + \u03b2*t + \u03b3*y_(t-1) + \u03b4_1*\u0394y_(t-1) + ... + \u03b5_t
  
  Interpretation:
    p-value < 0.05: STATIONARY (mean-reverting, good for trading)
    p-value \u2265 0.05: NON-STATIONARY (trending, avoid pairs trading)
        """)
        
        if spread_series:
            tester = StationarityTester()
            adf_result = tester.adf_test(spread_series)
            
            result_5 = {
                "adf_statistic": round(adf_result["adf_statistic"], 4),
                "p_value": round(adf_result["p_value"], 4),
                "stationary": adf_result["stationary"]
            }
            
            print("  Output:")
            print("  " + json.dumps(result_5, indent=2))
            
            # Show critical values
            if "critical_values" in adf_result:
                print("\n  Critical Values:")
                for level, value in adf_result["critical_values"].items():
                    print(f"    {level}: {value:.4f}")
            
            # Interpretation
            print(f"\n  {adf_result.get('interpretation', '')}")
            
            if adf_result["stationary"]:
                print("  ✅ Spread exhibits mean reversion \u2192 Suitable for pairs trading")
            else:
                print("  ⚠️  Spread is trending \u2192 Pairs trading strategy may be risky")
        
        # ====================================================================
        # SUMMARY
        # ====================================================================
        print("\n" + "="*70)
        print("  📊 ANALYTICS SUMMARY")
        print("="*70)
        
        # Safe formatting with None checks
        hr = hedge_ratio if hedge_ratio is not None else 0.0
        ls = latest_spread if latest_spread is not None else 0.0
        zs = zscore if zscore is not None else 0.0
        corr = correlation if correlation is not None else 0.0
        
        print(f"""
  Hedge Ratio:       {hr:.4f}
  Latest Spread:     {ls:.2f}
  Z-Score:           {zs:.2f}
  Correlation:       {corr:.4f}
  ADF p-value:       {adf_result['p_value']:.4f}
  Stationary:        {adf_result['stationary']}
  
  Trading Strategy Assessment:
  {'✅' if corr > 0.8 else '⚠️ '} Correlation: {"Strong" if corr > 0.8 else "Moderate/Weak"}
  {'✅' if adf_result['stationary'] else '⚠️ '} Stationarity: {"Yes" if adf_result['stationary'] else "No"}
  {'✅' if abs(zs) < 3 else '⚠️ '} Current Z-Score: {"Normal range" if abs(zs) < 3 else "Extreme"}
        """)
        
        print("="*70)
        print("  ✅ Analytics Engine Test Complete")
        print("  ⭐⭐⭐⭐⭐⭐ Gemscap Score Impact")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
        await client.stop()
        client_task.cancel()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await client.stop()
        client_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
