"""
Background task to finalize minute bars when the minute ends.
Ensures bars are stored even if no ticks arrive at the exact minute boundary.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from app.resampling import get_resampling_engine

logger = logging.getLogger(__name__)


class MinuteBarFinalizer:
    """
    Ensures minute bars are finalized and stored at minute boundaries.
    """
    
    def __init__(self, check_interval: float = 1.0):
        """
        Args:
            check_interval: How often to check for bars to finalize (seconds)
        """
        self.check_interval = check_interval
        self.running = False
        self.resampling = get_resampling_engine()
        logger.info("MinuteBarFinalizer initialized")
    
    async def start(self):
        """Start the finalizer task."""
        self.running = True
        asyncio.create_task(self._run())
    
    async def stop(self):
        """Stop the finalizer task."""
        self.running = False
    
    async def _run(self):
        """Main loop that checks and finalizes bars."""
        logger.info("MinuteBarFinalizer started")
        
        while self.running:
            try:
                await self._check_and_finalize()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in MinuteBarFinalizer: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _check_and_finalize(self):
        """Check for bars that need to be finalized."""
        current_time = datetime.now(timezone.utc)
        current_minute = current_time.replace(second=0, microsecond=0)
        
        # Previous minute (bars that should be finalized)
        previous_minute = current_minute - timedelta(minutes=1)
        
        # Check each symbol with an incomplete bar
        symbols_to_finalize = []
        
        for symbol, bar in self.resampling.current_minute_bar.items():
            if bar.timestamp < previous_minute:
                # This bar is from at least 2 minutes ago, finalize it
                symbols_to_finalize.append(symbol)
            elif bar.timestamp == previous_minute:
                # This bar is from the previous minute, check if we should finalize
                # Wait 5 seconds into the new minute to ensure all ticks are processed
                if current_time.second > 5:
                    symbols_to_finalize.append(symbol)
        
        # Finalize bars
        for symbol in symbols_to_finalize:
            await self._finalize_bar(symbol)
    
    async def _finalize_bar(self, symbol: str):
        """Finalize and store a minute bar."""
        if symbol not in self.resampling.current_minute_bar:
            return
        
        bar = self.resampling.current_minute_bar[symbol]
        
        # Store in complete bars
        if symbol not in self.resampling.minute_bars:
            self.resampling.minute_bars[symbol] = []
        
        # Check if already stored
        if not self.resampling._bar_exists(self.resampling.minute_bars.get(symbol, []), bar.timestamp):
            self.resampling.minute_bars[symbol].append(bar)
            
            # Trim if needed
            if len(self.resampling.minute_bars[symbol]) > self.resampling.max_bars_per_symbol:
                self.resampling.minute_bars[symbol] = self.resampling.minute_bars[symbol][-self.resampling.max_bars_per_symbol:]
            
            logger.info(f"[Finalizer] Stored minute bar for {symbol} at {bar.timestamp}. "
                       f"Total bars: {len(self.resampling.minute_bars[symbol])}")
        
        # Remove from current bars
        del self.resampling.current_minute_bar[symbol]


# Singleton instance
_minute_bar_finalizer = None

def get_minute_bar_finalizer() -> MinuteBarFinalizer:
    """Get the singleton MinuteBarFinalizer instance."""
    global _minute_bar_finalizer
    if _minute_bar_finalizer is None:
        _minute_bar_finalizer = MinuteBarFinalizer()
    return _minute_bar_finalizer
