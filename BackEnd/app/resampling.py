"""
Resampling engine for converting ticks to time bars.
Handles 1-second, 1-minute, and other interval bars.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class Bar:
    """OHLCV bar structure."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    interval: str


class ResamplingEngine:
    """
    Converts tick data to OHLCV bars at various intervals.
    """
    
    def __init__(self):
        # Store complete bars
        self.second_bars: Dict[str, List[Bar]] = {}
        self.minute_bars: Dict[str, List[Bar]] = {}
        
        # Track current incomplete bars
        self.current_second_bar: Dict[str, Bar] = {}
        self.current_minute_bar: Dict[str, Bar] = {}
        
        # Store bar timestamps for deduplication
        self.last_second_timestamp: Dict[str, datetime] = {}
        self.last_minute_timestamp: Dict[str, datetime] = {}
        
        # Maximum bars to keep
        self.max_bars_per_symbol = 1000
        
        logger.info("ResamplingEngine initialized")
    
    async def process_ticks(self, ticks: List, symbol: str):
        """
        Process incoming ticks and create/update bars.
        
        Args:
            ticks: List of tick objects
            symbol: Trading symbol
        """
        if not ticks:
            return
        
        for tick in ticks:
            await self._process_tick(tick, symbol)
    
    async def _process_tick(self, tick, symbol: str):
        """Process a single tick."""
        tick_time = pd.to_datetime(tick.timestamp)
        
        # Process 1-second bars
        await self._process_second_bar(tick, symbol, tick_time)
        
        # Process 1-minute bars
        await self._process_minute_bar(tick, symbol, tick_time)
    
    async def _process_second_bar(self, tick, symbol: str, tick_time: datetime):
        """Handle 1-second bar creation/update."""
        # Floor to second
        second_start = tick_time.replace(microsecond=0)
        
        # Check if this is a new second
        if symbol not in self.current_second_bar or \
           self.current_second_bar[symbol].timestamp != second_start:
            
            # Store previous second's bar if it exists
            if symbol in self.current_second_bar:
                stored_bar = self.current_second_bar[symbol]
                if symbol not in self.second_bars:
                    self.second_bars[symbol] = []
                
                # Only add if not already stored
                if not self._bar_exists(self.second_bars.get(symbol, []), stored_bar.timestamp):
                    self.second_bars[symbol].append(stored_bar)
                    
                    # Trim if needed
                    if len(self.second_bars[symbol]) > self.max_bars_per_symbol:
                        self.second_bars[symbol] = self.second_bars[symbol][-self.max_bars_per_symbol:]
            
            # Create new second bar
            self.current_second_bar[symbol] = Bar(
                timestamp=second_start,
                open=tick.price,
                high=tick.price,
                low=tick.price,
                close=tick.price,
                volume=tick.qty,
                symbol=symbol,
                interval='1s'
            )
        else:
            # Update existing second bar
            current_bar = self.current_second_bar[symbol]
            current_bar.high = max(current_bar.high, tick.price)
            current_bar.low = min(current_bar.low, tick.price)
            current_bar.close = tick.price
            current_bar.volume += tick.qty
    
    async def _process_minute_bar(self, tick, symbol: str, tick_time: datetime):
        """Handle 1-minute bar creation/update - CRITICAL FIX HERE."""
        # Floor to minute
        minute_start = tick_time.replace(second=0, microsecond=0)
        
        # CRITICAL FIX: Check if we need to finalize previous minute
        if symbol in self.current_minute_bar:
            current_bar = self.current_minute_bar[symbol]
            
            # If we've moved to a new minute, finalize the old one
            if current_bar.timestamp < minute_start:
                # Store the completed bar
                if symbol not in self.minute_bars:
                    self.minute_bars[symbol] = []
                
                # Only add if not already stored
                if not self._bar_exists(self.minute_bars.get(symbol, []), current_bar.timestamp):
                    self.minute_bars[symbol].append(current_bar)
                    
                    # Trim if needed
                    if len(self.minute_bars[symbol]) > self.max_bars_per_symbol:
                        self.minute_bars[symbol] = self.minute_bars[symbol][-self.max_bars_per_symbol:]
                    
                    # Log bar finalization (only every 5 bars to reduce spam)
                    total_bars = len(self.minute_bars[symbol])
                    if total_bars % 5 == 0 or total_bars <= 3:
                        bar_time = current_bar.timestamp.strftime('%H:%M:%S')
                        logger.info(f"[{symbol}] ✓ Bar #{total_bars} finalized ({bar_time}) | C:{current_bar.close:.2f} V:{current_bar.volume:.2f}")
                
                # Clear current bar - we'll create a new one below
                del self.current_minute_bar[symbol]
        
        # Now handle the current minute
        if symbol not in self.current_minute_bar:
            # Create new minute bar
            self.current_minute_bar[symbol] = Bar(
                timestamp=minute_start,
                open=tick.price,
                high=tick.price,
                low=tick.price,
                close=tick.price,
                volume=tick.qty,
                symbol=symbol,
                interval='1m'
            )
            # Only log first bar or after gaps
            if not hasattr(self, '_bars_created'):
                self._bars_created = set()
            if symbol not in self._bars_created:
                self._bars_created.add(symbol)
                bar_time = minute_start.strftime('%H:%M:%S')
                logger.info(f"[{symbol}] 🟢 Started collecting bars (first bar: {bar_time})")
        else:
            # Update existing minute bar (same minute)
            current_bar = self.current_minute_bar[symbol]
            current_bar.high = max(current_bar.high, tick.price)
            current_bar.low = min(current_bar.low, tick.price)
            current_bar.close = tick.price
            current_bar.volume += tick.qty
    
    def _bar_exists(self, bar_list: List[Bar], timestamp: datetime) -> bool:
        """Check if a bar with given timestamp already exists."""
        return any(bar.timestamp == timestamp for bar in bar_list)
    
    async def get_bars(self, symbol: str, interval: str = '1m', n: int = 60) -> List[Dict[str, Any]]:
        """
        Get bars for a symbol and interval.
        
        Args:
            symbol: Trading symbol
            interval: Time interval ('1s', '1m', etc.)
            n: Number of bars to return
            
        Returns:
            List of bar dictionaries
        """
        if interval == '1m':
            # Get stored complete bars
            stored_bars = self.minute_bars.get(symbol, [])
            
            # Get current incomplete bar (if exists)
            current_bar = self.current_minute_bar.get(symbol)
            
            # Convert bars to dictionaries
            result = []
            
            # Add stored bars
            for bar in stored_bars:
                result.append({
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                    'symbol': bar.symbol
                })
            
            # Add current incomplete bar if it exists
            if current_bar:
                result.append({
                    'timestamp': current_bar.timestamp,
                    'open': current_bar.open,
                    'high': current_bar.high,
                    'low': current_bar.low,
                    'close': current_bar.close,
                    'volume': current_bar.volume,
                    'symbol': current_bar.symbol
                })
            
            # Sort by timestamp (oldest first)
            result.sort(key=lambda x: x['timestamp'])
            
            # Get last n bars
            result = result[-n:] if len(result) > n else result
            
            # Log the count
            stored_count = len(stored_bars)
            has_current = 1 if current_bar else 0
            total_count = stored_count + has_current
            
            # Only log significant milestones (first bar, every 10 bars, or when reaching 30)
            if not hasattr(self, '_last_logged_count'):
                self._last_logged_count = {}
            
            last_count = self._last_logged_count.get(symbol, -1)
            if stored_count != last_count and (stored_count == 0 or stored_count == 1 or stored_count % 10 == 0 or stored_count == 30):
                self._last_logged_count[symbol] = stored_count
                if stored_count == 0 and has_current:
                    bar_time = current_bar.timestamp.strftime('%H:%M:%S') if current_bar else 'N/A'
                    logger.info(f"[{symbol}] 📈 Building first bar at {bar_time}...")
                elif stored_count > 0:
                    logger.info(f"[{symbol}] 📊 Progress: {stored_count} complete bars (+ {has_current} current)")
            
            return result
        
        elif interval == '1s':
            # Similar logic for 1-second bars
            stored_bars = self.second_bars.get(symbol, [])
            current_bar = self.current_second_bar.get(symbol)
            
            result = []
            for bar in stored_bars:
                result.append({
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                    'symbol': bar.symbol
                })
            
            if current_bar:
                result.append({
                    'timestamp': current_bar.timestamp,
                    'open': current_bar.open,
                    'high': current_bar.high,
                    'low': current_bar.low,
                    'close': current_bar.close,
                    'volume': current_bar.volume,
                    'symbol': current_bar.symbol
                })
            
            result.sort(key=lambda x: x['timestamp'])
            result = result[-n:] if len(result) > n else result
            
            return result
        
        return []
    
    async def get_price_history(self, symbols: List[str], interval: str = '1m', n: int = 60) -> List[Dict[str, Any]]:
        """
        Get price history for multiple symbols.
        
        Args:
            symbols: List of symbols
            interval: Time interval
            n: Number of bars per symbol
            
        Returns:
            List of bar dictionaries with all symbols
        """
        if not symbols:
            return []
        
        # Get bars for each symbol
        all_bars = {}
        for symbol in symbols:
            bars = await self.get_bars(symbol, interval, n)
            all_bars[symbol] = bars
        
        # Find common timestamps (align by index)
        min_length = min(len(bars) for bars in all_bars.values())
        if min_length == 0:
            return []
        
        # Create combined bars
        result = []
        for i in range(-min_length, 0):  # Get last min_length bars
            combined_bar = {'timestamp': None}
            
            for symbol in symbols:
                bars = all_bars[symbol]
                if len(bars) >= abs(i):
                    bar = bars[i]
                    if combined_bar['timestamp'] is None:
                        combined_bar['timestamp'] = bar['timestamp']
                    
                    combined_bar[symbol] = bar['close']
            
            if combined_bar['timestamp'] is not None:
                result.append(combined_bar)
        
        return result
    
    def clear(self, symbol: str = None):
        """Clear bars for a symbol or all symbols."""
        if symbol:
            if symbol in self.second_bars:
                del self.second_bars[symbol]
            if symbol in self.minute_bars:
                del self.minute_bars[symbol]
            if symbol in self.current_second_bar:
                del self.current_second_bar[symbol]
            if symbol in self.current_minute_bar:
                del self.current_minute_bar[symbol]
        else:
            self.second_bars.clear()
            self.minute_bars.clear()
            self.current_second_bar.clear()
            self.current_minute_bar.clear()


# Singleton instance
_resampling_engine = None

def get_resampling_engine() -> ResamplingEngine:
    """Get the singleton ResamplingEngine instance."""
    global _resampling_engine
    if _resampling_engine is None:
        _resampling_engine = ResamplingEngine()
    return _resampling_engine
