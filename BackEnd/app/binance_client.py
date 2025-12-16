"""
Binance Futures WebSocket client for live tick data ingestion.
Manages connections to Binance Futures trade streams and handles reconnections.
"""
import asyncio
import json
import logging
from typing import Callable, List, Optional, Set
from datetime import datetime
import websockets
from websockets.client import WebSocketClientProtocol

from app.schemas import TickData
from app.settings import settings

logger = logging.getLogger(__name__)


class BinanceClient:
    """
    WebSocket client for Binance Futures real-time trade data.
    Connects to multiple symbol streams and handles automatic reconnection.
    
    Binance Futures WebSocket API:
    - Base URL: wss://fstream.binance.com/ws
    - Stream format: <symbol>@trade (e.g., btcusdt@trade)
    - Multi-stream: wss://fstream.binance.com/stream?streams=btcusdt@trade/ethusdt@trade
    """
    
    def __init__(self, symbols: Optional[List[str]] = None):
        """
        Initialize Binance Futures client.
        
        Args:
            symbols: List of trading symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
        """
        self.symbols: Set[str] = set(symbols or settings.DEFAULT_SYMBOLS)
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.is_running: bool = False
        self.reconnect_delay: int = 5  # Seconds between reconnection attempts
        self.callbacks: List[Callable[[TickData], None]] = []
        self.message_count: int = 0
        self.last_message_time: Optional[datetime] = None
        
    def subscribe_to_ticks(self, callback: Callable[[TickData], None]):
        """
        Register a callback to receive tick data.
        
        Args:
            callback: Function that receives TickData objects
        """
        self.callbacks.append(callback)
        logger.info(f"Registered tick callback: {callback.__name__}")
    
    def add_symbol(self, symbol: str):
        """Add a new symbol to track."""
        symbol = symbol.upper()
        if symbol not in self.symbols:
            self.symbols.add(symbol)
            logger.info(f"Added symbol: {symbol}")
            # TODO: Dynamically resubscribe if already connected
    
    def remove_symbol(self, symbol: str):
        """Remove a symbol from tracking."""
        symbol = symbol.upper()
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            logger.info(f"Removed symbol: {symbol}")
    
    def _build_stream_url(self) -> str:
        """
        Build the Binance Futures WebSocket URL for multi-stream subscription.
        
        Returns:
            WebSocket URL string for Binance Futures
        """
        # Binance Futures multi-stream format
        # wss://fstream.binance.com/stream?streams=btcusdt@trade/ethusdt@trade/solusdt@trade
        if not self.symbols:
            raise ValueError("No symbols configured for streaming")
        
        # Convert symbols to lowercase for stream names
        streams = "/".join([f"{s.lower()}@trade" for s in self.symbols])
        
        # Use Binance Futures WebSocket endpoint
        return f"wss://fstream.binance.com/stream?streams={streams}"
    
    async def _handle_message(self, message: str):
        """
        Parse and dispatch incoming Binance Futures trade messages.
        
        Binance Futures trade message format:
        {
            "stream": "btcusdt@trade",
            "data": {
                "e": "trade",           // Event type
                "E": 1672515782136,     // Event time
                "T": 1672515782134,     // Trade time
                "s": "BTCUSDT",         // Symbol
                "t": 12345,             // Trade ID
                "p": "16888.12",        // Price
                "q": "0.100",           // Quantity
                "X": "MARKET",          // Order type
                "m": true               // Is buyer maker
            }
        }
        
        Args:
            message: Raw JSON message from Binance Futures
        """
        try:
            data = json.loads(message)
            
            # Binance Futures multi-stream wrapper
            if "stream" in data and "data" in data:
                trade_data = data["data"]
                
                # Validate trade event
                if trade_data.get("e") != "trade":
                    logger.debug(f"Ignoring non-trade event: {trade_data.get('e')}")
                    return
                
                # Skip liquidation/insurance fund trades (order type 'NA' with 0 price/qty)
                order_type = trade_data.get("X", "")
                if order_type == "NA":
                    return
                
                # Extract and normalize trade data
                symbol = trade_data.get("s", "").upper()
                
                # Validate symbol is in our tracked list
                if symbol not in self.symbols:
                    logger.warning(f"Received data for untracked symbol: {symbol}")
                    return
                
                try:
                    # Parse price and quantity as floats
                    price_str = trade_data.get("p")
                    quantity_str = trade_data.get("q")
                    
                    # Validate fields exist
                    if price_str is None:
                        logger.warning(f"Missing price field for {symbol}. Full message: {trade_data}")
                        return
                    
                    if quantity_str is None:
                        logger.warning(f"Missing quantity field for {symbol}. Full message: {trade_data}")
                        return
                    
                    price = float(price_str)
                    quantity = float(quantity_str)
                    
                    # Use trade time (T) not event time (E) for accuracy
                    timestamp_ms = int(trade_data.get("T", 0))
                    
                    # Validate data
                    if price <= 0:
                        logger.warning(f"Invalid price for {symbol}: {price}. Full message: {trade_data}")
                        return
                    
                    if timestamp_ms <= 0:
                        logger.warning(f"Invalid timestamp for {symbol}: {timestamp_ms}")
                        return
                    
                    # Convert unix timestamp (ms) to ISO 8601 format
                    timestamp_iso = datetime.utcfromtimestamp(timestamp_ms / 1000.0).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                    
                    # Create normalized tick data
                    tick = TickData(
                        symbol=symbol,
                        price=price,
                        timestamp=timestamp_iso,
                        qty=quantity
                    )
                    
                    # Update statistics
                    self.message_count += 1
                    self.last_message_time = datetime.utcnow()
                    
                    # Log every 500th message for monitoring (reduced spam)
                    if self.message_count % 500 == 0:
                        logger.info(
                            f"📡 Processed {self.message_count} trades | "
                            f"Latest: {symbol} @ ${price:,.2f}"
                        )
                    
                    # Dispatch to all registered callbacks
                    for callback in self.callbacks:
                        try:
                            callback(tick)
                        except Exception as e:
                            logger.error(
                                f"Error in tick callback for {symbol}: {e}",
                                exc_info=True
                            )
                
                except (ValueError, TypeError) as e:
                    logger.error(f"Data parsing error for {symbol}: {e}")
                    logger.debug(f"Problematic data: {trade_data}")
                    
            else:
                # Handle non-standard messages (e.g., ping/pong)
                logger.debug(f"Received non-trade message: {data}")
                        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON message: {e}")
            logger.debug(f"Raw message: {message[:200]}...")
        except Exception as e:
            logger.error(f"Unexpected error handling message: {e}", exc_info=True)
    
    async def _connect_and_listen(self):
        """
        Establish WebSocket connection to Binance Futures and listen for trade messages.
        Handles reconnection on failure with exponential backoff.
        """
        url = self._build_stream_url()
        logger.info(f"Connecting to Binance Futures...")
        logger.info(f"  URL: {url}")
        logger.info(f"  Symbols: {', '.join(sorted(self.symbols))}")
        
        try:
            # Connect with timeout and compression
            async with websockets.connect(
                url,
                ping_interval=20,  # Send ping every 20s to keep connection alive
                ping_timeout=10,   # Wait 10s for pong response
                close_timeout=5,   # Timeout for close handshake
            ) as websocket:
                self.websocket = websocket
                logger.info("✓ Connected to Binance Futures successfully")
                logger.info(f"✓ Streaming trades for {len(self.symbols)} symbols")
                
                # Listen for messages indefinitely
                async for message in websocket:
                    if not self.is_running:
                        logger.info("Stop signal received, breaking message loop")
                        break
                    await self._handle_message(message)
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e.code} - {e.reason}")
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket exception: {e}", exc_info=True)
        except asyncio.TimeoutError:
            logger.error("Connection timeout - Binance Futures unreachable")
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket connection: {e}", exc_info=True)
        finally:
            self.websocket = None
            logger.info("WebSocket connection closed")
    
    async def start(self):
        """
        Start the Binance Futures WebSocket client with automatic reconnection.
        Runs indefinitely until stop() is called.
        
        Implements exponential backoff for reconnection attempts.
        """
        self.is_running = True
        logger.info("=" * 70)
        logger.info("Starting Binance Futures WebSocket Client")
        logger.info("=" * 70)
        
        reconnect_attempt = 0
        max_reconnect_delay = 60  # Maximum 60 seconds between attempts
        
        while self.is_running:
            try:
                await self._connect_and_listen()
                # Reset reconnect attempt counter on successful connection
                reconnect_attempt = 0
            except Exception as e:
                logger.error(f"Fatal connection error: {e}", exc_info=True)
            
            # Reconnect with exponential backoff if still running
            if self.is_running:
                reconnect_attempt += 1
                # Exponential backoff: 5s, 10s, 20s, 40s, 60s (max)
                delay = min(
                    self.reconnect_delay * (2 ** (reconnect_attempt - 1)),
                    max_reconnect_delay
                )
                logger.info(
                    f"Reconnection attempt #{reconnect_attempt} in {delay} seconds..."
                )
                await asyncio.sleep(delay)
    
    async def stop(self):
        """Stop the Binance Futures WebSocket client gracefully."""
        logger.info("Stopping Binance Futures WebSocket client...")
        self.is_running = False
        
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            finally:
                self.websocket = None
        
        logger.info("✓ Binance Futures client stopped")
        logger.info(f"✓ Total messages processed: {self.message_count}")
    
    def is_connected(self) -> bool:
        """Check if the WebSocket is currently connected to Binance Futures."""
        return self.websocket is not None and self.websocket.open
    
    def get_stats(self) -> dict:
        """
        Get client statistics.
        
        Returns:
            Dictionary with connection stats
        """
        return {
            "is_connected": self.is_connected(),
            "symbols": list(self.symbols),
            "message_count": self.message_count,
            "last_message_time": self.last_message_time.isoformat() if self.last_message_time else None,
            "callback_count": len(self.callbacks),
        }


# Global client instance
_binance_client: Optional[BinanceClient] = None


def get_binance_client() -> BinanceClient:
    """Get or create the global Binance client instance."""
    global _binance_client
    if _binance_client is None:
        _binance_client = BinanceClient()
    return _binance_client
