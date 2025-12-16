"""
Inspect in-memory tick storage structure.
Shows how tick data is stored and converts to DataFrame format.
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
from app.schemas import TickData


async def main():
    """Run the inspection."""
    print("\n" + "="*70)
    print("  📊 In-Memory Tick Storage Inspector")
    print("="*70)
    print("  Collecting 50 ticks from Binance Futures...")
    print("="*70 + "\n")
    
    # Initialize components
    ingestion_engine = get_ingestion_engine()
    client = BinanceClient()
    
    # Connect ingestion to Binance client
    client.subscribe_to_ticks(lambda tick: asyncio.create_task(ingestion_engine.ingest_tick(tick)))
    
    # Start client in background
    client_task = asyncio.create_task(client.start())
    
    # Collect ticks for a few seconds
    tick_count = 0
    target_ticks = 50
    
    try:
        while True:
            await asyncio.sleep(0.5)
            stats = await ingestion_engine.get_buffer_stats()
            tick_count = sum(s.get("buffer_size", 0) for s in stats.values())
            
            if tick_count >= target_ticks:
                break
                
            print(f"  Collecting... {tick_count}/{target_ticks} ticks", end="\r")
        
        print(f"\n\n✓ Collected {tick_count} ticks!")
        
        # Stop client
        await client.stop()
        client_task.cancel()
        
        # Display in-memory structure
        print("\n" + "="*70)
        print("  📊 IN-MEMORY STRUCTURE")
        print("="*70)
        
        symbols = ingestion_engine.get_active_symbols()
        
        for symbol in sorted(symbols):
            print(f"\n{'─'*70}")
            print(f"  Symbol: {symbol}")
            print(f"{'─'*70}")
            
            # Get all ticks for this symbol
            ticks = await ingestion_engine.get_tick_history(symbol)
            
            if not ticks:
                print("  No data")
                continue
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    "timestamp": tick.timestamp,
                    "price": tick.price,
                    "qty": tick.qty
                }
                for tick in ticks
            ])
            
            # Show buffer stats
            buffer_stats = await ingestion_engine.buffers[symbol].get_stats()
            print(f"\n  Buffer Stats:")
            print(f"    - Total ticks stored: {buffer_stats['buffer_size']}")
            print(f"    - Total ingested: {buffer_stats['total_ticks']}")
            print(f"    - Latest price: ${buffer_stats['last_price']:,.2f}")
            
            # Show DataFrame structure
            print(f"\n  DataFrame Structure:")
            print(f"    - Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"    - Memory usage: ~{df.memory_usage(deep=True).sum() / 1024:.2f} KB")
            print(f"    - Columns: {list(df.columns)}")
            
            # Show sample data
            print(f"\n  📊 Sample Data (First 10 rows):")
            print("  " + "─"*66)
            
            # Format for display
            sample = df.head(10).copy()
            
            # Create display table
            print(f"  {'#':<4} {'Timestamp':<28} {'Price':>12} {'Qty':>10}")
            print("  " + "─"*66)
            
            for idx, row in sample.iterrows():
                print(f"  {idx:<4} {row['timestamp']:<28} {row['price']:>12,.2f} {row['qty']:>10.4f}")
            
            if len(df) > 10:
                print(f"  ... ({len(df) - 10} more rows)")
        
        # Show overall memory stats
        print("\n" + "="*70)
        print("  💾 OVERALL MEMORY USAGE")
        print("="*70)
        
        total_ticks = 0
        for s in symbols:
            ticks = await ingestion_engine.get_tick_history(s)
            total_ticks += len(ticks)
        
        estimated_memory = total_ticks * 100  # ~100 bytes per tick
        
        print(f"\n  Total symbols: {len(symbols)}")
        print(f"  Total ticks in memory: {total_ticks:,}")
        print(f"  Estimated memory: ~{estimated_memory / 1024:.2f} KB")
        
        # Show how to access as DataFrames
        print("\n" + "="*70)
        print("  🔧 PROGRAMMATIC ACCESS")
        print("="*70)
        print("""
  # Get all ticks for a symbol
  ticks = await ingestion_engine.get_tick_history("BTCUSDT")
  
  # Convert to DataFrame
  df = pd.DataFrame([{
      "timestamp": tick.timestamp,
      "price": tick.price,
      "qty": tick.qty
  } for tick in ticks])
  
  # In-memory structure
  memory_structure = {
      symbol: pd.DataFrame([
          {"timestamp": t.timestamp, "price": t.price, "qty": t.qty}
          for t in await ingestion_engine.get_tick_history(symbol)
      ])
      for symbol in ingestion_engine.get_active_symbols()
  }
        """)
        
        print("="*70)
        print("  ✅ Inspection Complete")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
        await client.stop()
        client_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
