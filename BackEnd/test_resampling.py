"""
Test resampling: Tick → OHLCV bars (1s, 1m, 5m)
Shows how tick data is converted to candlestick bars.
"""
import asyncio
import sys
import os
from datetime import datetime
import pandas as pd

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.binance_client import BinanceClient
from app.ingestion import get_ingestion_engine
from app.resampling import get_resampling_engine


async def main():
    """Test resampling."""
    print("\n" + "="*70)
    print("  🕐 Testing Resampling: Tick → OHLCV Bars")
    print("="*70)
    print("  Timeframes: 1s, 1m, 5m")
    print("  Collecting ticks for 30 seconds...")
    print("="*70 + "\n")
    
    # Initialize components
    ingestion = get_ingestion_engine()
    resampling = get_resampling_engine()
    client = BinanceClient()
    
    # Connect pipeline: Binance → Ingestion → Resampling
    async def handle_tick(tick):
        await ingestion.ingest_tick(tick)
        # Also feed to resampling (get recent ticks)
        ticks = await ingestion.get_tick_history(tick.symbol, n=1000)
        await resampling.process_ticks(ticks, tick.symbol)
    
    client.subscribe_to_ticks(lambda tick: asyncio.create_task(handle_tick(tick)))
    
    # Start client
    client_task = asyncio.create_task(client.start())
    
    try:
        # Collect for 30 seconds
        print("  ⏳ Collecting data...\n")
        await asyncio.sleep(30)
        
        # Stop client
        await client.stop()
        client_task.cancel()
        
        print("\n✓ Collection complete!\n")
        
        # Display resampled data for each symbol
        symbols = ingestion.get_active_symbols()
        
        for symbol in sorted(symbols):
            print("\n" + "="*70)
            print(f"  📊 {symbol} - OHLCV Bars")
            print("="*70)
            
            # Test each timeframe
            for interval in ['1s', '1m', '5m']:
                bars = await resampling.get_bars(symbol, interval, n=5)
                
                if not bars:
                    continue
                
                print(f"\n  ⏱️  Timeframe: {interval}")
                print("  " + "─"*66)
                print(f"  {'Timestamp':<20} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>10}")
                print("  " + "─"*66)
                
                for bar in bars:
                    print(f"  {bar.timestamp:<20} {bar.open:>10,.2f} {bar.high:>10,.2f} "
                          f"{bar.low:>10,.2f} {bar.close:>10,.2f} {bar.volume:>10.4f}")
                
                print(f"  " + "─"*66)
                print(f"  Total bars: {len(bars)}")
        
        # Show how to use as DataFrame
        print("\n" + "="*70)
        print("  📈 Convert to DataFrame (Example)")
        print("="*70)
        
        symbol = symbols[0] if symbols else "BTCUSDT"
        bars = await resampling.get_bars(symbol, "1m", n=10)
        
        if bars:
            df = pd.DataFrame([
                {
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                }
                for bar in bars
            ])
            
            print(f"\n  DataFrame shape: {df.shape}")
            print(f"  Columns: {list(df.columns)}")
            print(f"\n{df.to_string(index=False)}")
        
        # Explain incremental updates
        print("\n" + "="*70)
        print("  ⚡ Incremental Updates (No Full Recomputation)")
        print("="*70)
        print("""
  How it works:
  
  1. New ticks arrive → Added to ingestion buffer
  2. Resampling engine processes last 1000 ticks
  3. Only new/updated bars are computed
  4. Maintains fixed-size rolling window (100 bars/timeframe)
  5. No full history recomputation needed
  
  Efficiency:
  - Tick arrives: ~0.1ms (append to deque)
  - Resample 1000 ticks: ~5-10ms (pandas resample)
  - Memory: ~5KB per symbol per timeframe
  
  Code:
    # Get bars for any timeframe
    bars = await resampling_engine.get_bars(
        symbol="BTCUSDT",
        interval="1m",  # 1s, 1m, 5m, 15m, 1h
        n=50  # Last 50 bars
    )
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'timestamp': b.timestamp,
        'open': b.open,
        'high': b.high,
        'low': b.low,
        'close': b.close,
        'volume': b.volume
    } for b in bars])
        """)
        
        print("="*70)
        print("  ✅ Resampling Test Complete")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
        await client.stop()
        client_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
