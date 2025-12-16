"""
WebSocket connection manager for frontend clients.
Handles broadcasting analytics data to connected frontends.
"""
import asyncio
import logging
from typing import Dict, Set, Optional
from datetime import datetime
import json

from fastapi import WebSocket, WebSocketDisconnect

from app.schemas import (
    PriceDataPoint,
    SpreadDataPoint,
    CorrelationDataPoint,
    SummaryStats,
    Alert,
    WSMessage
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections to frontend clients.
    Supports multiple connection types (prices, spread, correlation, summary).
    """
    
    def __init__(self):
        """Initialize connection manager."""
        # Separate connection pools for different data streams
        self.price_connections: Set[WebSocket] = set()
        self.spread_connections: Set[WebSocket] = set()
        self.correlation_connections: Set[WebSocket] = set()
        self.summary_connections: Set[WebSocket] = set()
        self.alert_connections: Set[WebSocket] = set()
        self.analytics_connections: Set[WebSocket] = set()  # Combined analytics stream
        
        # Track all connections
        self.all_connections: Dict[WebSocket, str] = {}  # ws -> stream_type
        
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, stream_type: str):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            stream_type: Type of data stream ('prices', 'spread', 'correlation', 'summary', 'alerts')
        """
        await websocket.accept()
        
        async with self.lock:
            # Add to appropriate connection pool
            if stream_type == "prices":
                self.price_connections.add(websocket)
            elif stream_type == "spread":
                self.spread_connections.add(websocket)
            elif stream_type == "correlation":
                self.correlation_connections.add(websocket)
            elif stream_type == "summary":
                self.summary_connections.add(websocket)
            elif stream_type == "alerts":
                self.alert_connections.add(websocket)
            elif stream_type == "analytics":
                self.analytics_connections.add(websocket)
            
            self.all_connections[websocket] = stream_type
            
            logger.info(f"✓ Frontend connected: {stream_type} (Total: {len(self.all_connections)})")
    
    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        async with self.lock:
            stream_type = self.all_connections.get(websocket, "unknown")
            
            # Remove from all pools
            self.price_connections.discard(websocket)
            self.spread_connections.discard(websocket)
            self.correlation_connections.discard(websocket)
            self.summary_connections.discard(websocket)
            self.alert_connections.discard(websocket)
            self.analytics_connections.discard(websocket)
            
            if websocket in self.all_connections:
                del self.all_connections[websocket]
            
            logger.info(f"✗ Frontend disconnected: {stream_type} (Total: {len(self.all_connections)})")
    
    async def broadcast_to_pool(
        self,
        connections: Set[WebSocket],
        message: dict
    ):
        """
        Broadcast a message to a specific connection pool.
        
        Args:
            connections: Set of WebSocket connections
            message: Message dictionary to broadcast
        """
        if not connections:
            return
        
        # Convert to JSON
        message_json = json.dumps(message)
        
        # Track failed connections for cleanup
        failed_connections = set()
        
        for connection in connections:
            try:
                await connection.send_text(message_json)
            except WebSocketDisconnect:
                failed_connections.add(connection)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                failed_connections.add(connection)
        
        # Clean up failed connections
        if failed_connections:
            async with self.lock:
                for conn in failed_connections:
                    await self.disconnect(conn)
    
    async def broadcast_prices(self, data: PriceDataPoint):
        """
        Broadcast price data to subscribed clients.
        
        Args:
            data: PriceDataPoint object
        """
        message = {
            "type": "prices",
            "data": data.model_dump(),
            "timestamp": int(datetime.utcnow().timestamp() * 1000)
        }
        await self.broadcast_to_pool(self.price_connections, message)
    
    async def broadcast_spread(self, data: SpreadDataPoint):
        """
        Broadcast spread/z-score data to subscribed clients.
        
        Args:
            data: SpreadDataPoint object
        """
        message = {
            "type": "spread",
            "data": data.model_dump(),
            "timestamp": int(datetime.utcnow().timestamp() * 1000)
        }
        await self.broadcast_to_pool(self.spread_connections, message)
    
    async def broadcast_correlation(self, data: CorrelationDataPoint):
        """
        Broadcast correlation data to subscribed clients.
        
        Args:
            data: CorrelationDataPoint object
        """
        message = {
            "type": "correlation",
            "data": data.model_dump(),
            "timestamp": int(datetime.utcnow().timestamp() * 1000)
        }
        await self.broadcast_to_pool(self.correlation_connections, message)
    
    async def broadcast_summary(self, data: SummaryStats):
        """
        Broadcast summary statistics to subscribed clients.
        
        Args:
            data: SummaryStats object
        """
        message = {
            "type": "summary",
            "data": data.model_dump(),
            "timestamp": int(datetime.utcnow().timestamp() * 1000)
        }
        await self.broadcast_to_pool(self.summary_connections, message)
    
    async def broadcast_alert(self, data: Alert):
        """
        Broadcast alert to subscribed clients.
        
        Args:
            data: Alert object
        """
        message = {
            "type": "alert",
            "data": data.model_dump(),
            "timestamp": int(datetime.utcnow().timestamp() * 1000)
        }
        await self.broadcast_to_pool(self.alert_connections, message)
    
    async def broadcast_analytics(
        self,
        timestamp: str,
        prices: dict,
        spread: float,
        z_score: float,
        correlation: float
    ):
        """
        Broadcast combined analytics to subscribed clients.
        
        Payload format:
        {
            "timestamp": "2025-01-01T12:31:00",
            "prices": {"BTCUSDT": 67521.45, "ETHUSDT": 3456.78},
            "spread": 12.45,
            "z_score": -0.68,
            "correlation": 0.889
        }
        
        Args:
            timestamp: ISO 8601 timestamp
            prices: Dictionary of symbol prices
            spread: Current spread value
            z_score: Current z-score
            correlation: Current correlation coefficient
        """
        message = {
            "timestamp": timestamp,
            "prices": prices,
            "spread": spread,
            "z_score": z_score,
            "correlation": correlation
        }
        await self.broadcast_to_pool(self.analytics_connections, message)
    
    async def broadcast_all(
        self,
        prices: Optional[PriceDataPoint] = None,
        spread: Optional[SpreadDataPoint] = None,
        correlation: Optional[CorrelationDataPoint] = None,
        summary: Optional[SummaryStats] = None
    ):
        """
        Broadcast multiple data types at once.
        
        Args:
            prices: Price data
            spread: Spread data
            correlation: Correlation data
            summary: Summary statistics
        """
        tasks = []
        
        if prices:
            tasks.append(self.broadcast_prices(prices))
        if spread:
            tasks.append(self.broadcast_spread(spread))
        if correlation:
            tasks.append(self.broadcast_correlation(correlation))
        if summary:
            tasks.append(self.broadcast_summary(summary))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.all_connections)
    
    def get_connection_stats(self) -> Dict[str, int]:
        """Get connection statistics by stream type."""
        return {
            "total": len(self.all_connections),
            "prices": len(self.price_connections),
            "spread": len(self.spread_connections),
            "correlation": len(self.correlation_connections),
            "summary": len(self.summary_connections),
            "alerts": len(self.alert_connections),
            "analytics": len(self.analytics_connections),
        }


# Global connection manager
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the global connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
