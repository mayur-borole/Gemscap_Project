"""
Tick data ingestion and buffering.
Maintains in-memory buffers of recent ticks for each symbol.
"""
import asyncio
import logging
from collections import deque
from typing import Dict, List, Optional
from datetime import datetime

from app.schemas import TickData
from app.settings import settings

logger = logging.getLogger(__name__)


class TickBuffer:
    """
    Thread-safe buffer for tick data with automatic size management.
    """
    
    def __init__(self, symbol: str, max_size: int = None):
        """
        Initialize tick buffer.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            max_size: Maximum number of ticks to store
        """
        self.symbol = symbol
        self.max_size = max_size or settings.TICK_BUFFER_SIZE
        self.ticks: deque[TickData] = deque(maxlen=self.max_size)
        self.lock = asyncio.Lock()
        self.last_tick: Optional[TickData] = None
        self.tick_count = 0
    
    async def add_tick(self, tick: TickData):
        """
        Add a new tick to the buffer.
        
        Args:
            tick: TickData object
        """
        async with self.lock:
            self.ticks.append(tick)
            self.last_tick = tick
            self.tick_count += 1
    
    async def get_latest(self, n: int = 1) -> List[TickData]:
        """
        Get the latest N ticks.
        
        Args:
            n: Number of ticks to retrieve
            
        Returns:
            List of TickData objects (newest last)
        """
        async with self.lock:
            return list(self.ticks)[-n:]
    
    async def get_all(self) -> List[TickData]:
        """Get all ticks in the buffer."""
        async with self.lock:
            return list(self.ticks)
    
    async def get_range(self, start_time: int, end_time: int) -> List[TickData]:
        """
        Get ticks within a time range.
        
        Args:
            start_time: Start timestamp (milliseconds)
            end_time: End timestamp (milliseconds)
            
        Returns:
            List of TickData objects in the time range
        """
        async with self.lock:
            return [
                tick for tick in self.ticks
                if start_time <= tick.timestamp <= end_time
            ]
    
    async def clear(self):
        """Clear all ticks from the buffer."""
        async with self.lock:
            self.ticks.clear()
            self.last_tick = None
    
    async def get_stats(self) -> Dict:
        """Get buffer statistics."""
        async with self.lock:
            return {
                "symbol": self.symbol,
                "buffer_size": len(self.ticks),
                "total_ticks": self.tick_count,
                "last_price": self.last_tick.price if self.last_tick else None,
                "last_timestamp": self.last_tick.timestamp if self.last_tick else None,
            }


class IngestionEngine:
    """
    Manages tick buffers for multiple symbols and coordinates data ingestion.
    """
    
    def __init__(self):
        """Initialize the ingestion engine."""
        self.buffers: Dict[str, TickBuffer] = {}
        self.start_time = datetime.utcnow()
    
    def get_or_create_buffer(self, symbol: str) -> TickBuffer:
        """
        Get existing buffer or create a new one for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            TickBuffer instance
        """
        if symbol not in self.buffers:
            self.buffers[symbol] = TickBuffer(symbol)
            logger.info(f"Created tick buffer for {symbol}")
        return self.buffers[symbol]
    
    async def ingest_tick(self, tick: TickData):
        """
        Ingest a single tick into the appropriate buffer.
        
        Args:
            tick: TickData object
        """
        buffer = self.get_or_create_buffer(tick.symbol)
        await buffer.add_tick(tick)
        
        # Optional: Log every Nth tick to avoid spam
        if buffer.tick_count % 1000 == 0:
            logger.debug(f"{tick.symbol}: {buffer.tick_count} ticks ingested")
    
    async def get_latest_prices(self, symbols: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Get the latest price for each symbol.
        
        Args:
            symbols: Optional list of symbols to query (all if None)
            
        Returns:
            Dictionary mapping symbol to latest price
        """
        prices = {}
        symbols_to_query = symbols or list(self.buffers.keys())
        
        for symbol in symbols_to_query:
            if symbol in self.buffers:
                buffer = self.buffers[symbol]
                if buffer.last_tick:
                    prices[symbol] = buffer.last_tick.price
        
        return prices
    
    async def get_buffer_stats(self) -> Dict[str, Dict]:
        """
        Get statistics for all buffers.
        
        Returns:
            Dictionary mapping symbol to buffer stats
        """
        stats = {}
        for symbol, buffer in self.buffers.items():
            stats[symbol] = await buffer.get_stats()
        return stats
    
    async def get_tick_history(
        self, 
        symbol: str, 
        n: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[TickData]:
        """
        Get tick history for a symbol.
        
        Args:
            symbol: Trading symbol
            n: Number of latest ticks to retrieve (if time range not specified)
            start_time: Start timestamp (milliseconds)
            end_time: End timestamp (milliseconds)
            
        Returns:
            List of TickData objects
        """
        if symbol not in self.buffers:
            return []
        
        buffer = self.buffers[symbol]
        
        if start_time and end_time:
            return await buffer.get_range(start_time, end_time)
        elif n:
            return await buffer.get_latest(n)
        else:
            return await buffer.get_all()
    
    def get_active_symbols(self) -> List[str]:
        """Get list of symbols currently being tracked."""
        return list(self.buffers.keys())
    
    async def clear_all(self):
        """Clear all tick buffers."""
        for buffer in self.buffers.values():
            await buffer.clear()
        logger.info("Cleared all tick buffers")


# Global ingestion engine instance
_ingestion_engine: Optional[IngestionEngine] = None


def get_ingestion_engine() -> IngestionEngine:
    """Get or create the global ingestion engine instance."""
    global _ingestion_engine
    if _ingestion_engine is None:
        _ingestion_engine = IngestionEngine()
    return _ingestion_engine
