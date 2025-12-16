"""
Test script to verify Binance tick data normalization output.
Run this to see the formatted tick data in real-time.
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.binance_client import BinanceClient
from app.schemas import TickData

# Configuration
MAX_TICKS = 10  # Stop after receiving this many ticks
tick_count = 0


def print_tick(tick: TickData):
    """Print formatted tick data."""
    global tick_count
    tick_count += 1
    
    # Convert to dict and pretty print
    tick_dict = {
        "timestamp": tick.timestamp,
        "symbol": tick.symbol,
        "price": tick.price,
        "qty": tick.qty
    }
    
    print(f"\n{'='*60}")
    print(f"📊 Tick #{tick_count}/{MAX_TICKS} ({datetime.now().strftime('%H:%M:%S')})")
    print(f"{'='*60}")
    print(json.dumps(tick_dict, indent=2))
    print(f"{'='*60}\n")


async def main():
    """Run the test."""
    global tick_count
    
    print("\n" + "="*70)
    print("  🔍 Testing Binance Tick Data Normalization")
    print("="*70)
    print(f"  Will collect {MAX_TICKS} ticks and automatically stop")
    print("="*70 + "\n")
    
    # Create client with default symbols
    client = BinanceClient()
    
    # Register callback to print each tick
    client.subscribe_to_ticks(print_tick)
    
    # Start client in background
    client_task = asyncio.create_task(client.start())
    
    try:
        # Wait until we receive enough ticks
        while tick_count < MAX_TICKS:
            await asyncio.sleep(0.1)
        
        # Stop the client
        print("\n✓ Received all test ticks, stopping...\n")
        await client.stop()
        client_task.cancel()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Manually stopped...")
        await client.stop()
        client_task.cancel()
    
    # Show summary
    print("="*70)
    print("  ✅ Test Completed Successfully")
    print("="*70)
    stats = client.get_stats()
    print(f"  Total ticks received: {stats['message_count']}")
    print(f"  Symbols tracked: {', '.join(stats['symbols'])}")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
