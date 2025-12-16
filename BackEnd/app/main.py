"""
FastAPI application entry point.
Coordinates all components and exposes REST/WebSocket APIs.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.settings import settings
from app.schemas import (
    ControlSettings,
    HealthCheck,
    ExportRequest,
    ExportResponse,
    Alert,
)
from app.binance_client import get_binance_client
from app.ingestion import get_ingestion_engine
from app.resampling import get_resampling_engine
from app.analytics import get_analytics_engine
from app.alerts import get_alert_manager
from app.websocket_manager import get_connection_manager
from app.minute_bar_finalizer import get_minute_bar_finalizer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
app_start_time = datetime.utcnow()
background_tasks = set()
current_settings = ControlSettings()


# ============================================================================
# Background Processing
# ============================================================================

async def analytics_processor():
    """
    Background task that processes analytics and broadcasts to frontend.
    Runs continuously at specified intervals.
    """
    logger.info("Starting analytics processor...")
    
    ingestion = get_ingestion_engine()
    resampling = get_resampling_engine()
    analytics = get_analytics_engine()
    alerts = get_alert_manager()
    ws_manager = get_connection_manager()
    
    while True:
        try:
            # Get latest tick prices immediately
            latest_ticks = await ingestion.get_latest_prices()
            logger.debug(f"Latest ticks: {latest_ticks}")
            
            # Build prices dict from latest ticks
            prices_dict = {}
            for symbol in current_settings.selectedSymbols:
                if symbol in latest_ticks:
                    prices_dict[symbol] = latest_ticks[symbol]
            logger.debug(f"Prices dict for selected symbols: {prices_dict}")
            
            # Initialize with safe fallback values
            spread = 0.0
            z_score = 0.0
            correlation = 0.0
            
            # Try to compute analytics if we have enough bars
            price_history = await resampling.get_price_history(
                symbols=current_settings.selectedSymbols,
                interval="1s",
                n=60
            )
            
            logger.debug(f"Price history: {len(price_history) if price_history else 0} bars available")
            
            if price_history and len(price_history) >= 2:
                # Compute analytics
                spread_data = await analytics.compute_spread_analysis(
                    price_history,
                    threshold=current_settings.zScoreThreshold,
                    regression_type=current_settings.regressionType
                )
                
                logger.debug(f"Spread data computed: {spread_data}")
                
                correlation_data = await analytics.compute_correlation(
                    price_history,
                    symbol_a=current_settings.selectedSymbols[0] if len(current_settings.selectedSymbols) > 0 else "BTCUSDT",
                    symbol_b=current_settings.selectedSymbols[1] if len(current_settings.selectedSymbols) > 1 else "ETHUSDT"
                )
                
                summary_stats = await analytics.compute_summary_stats(
                    price_history,
                    symbols=current_settings.selectedSymbols,
                    window=current_settings.windowSize
                )
                
                # Use computed values
                if spread_data:
                    spread = spread_data.spread
                    z_score = spread_data.zScore
                else:
                    logger.warning("spread_data is None - analytics could not be computed")
                if correlation_data:
                    correlation = correlation_data.correlation
                
                # Evaluate alerts
                if summary_stats:
                    await alerts.evaluate_summary_alerts(
                        summary_stats,
                        zscore_threshold=current_settings.zScoreThreshold
                    )
                
                # Broadcast to individual streams
                # Build PriceDataPoint from latest tick prices (not historical bars)
                latest_prices = None
                if prices_dict:
                    from app.schemas import PriceDataPoint
                    
                    # Build price data point with current tick prices
                    now = datetime.utcnow()
                    price_dict = {"timestamp": int(now.timestamp())}
                    price_dict["time"] = now.strftime("%H:%M:%S")
                    
                    # Add current tick prices for each symbol
                    for symbol, price in prices_dict.items():
                        price_dict[symbol] = price
                    
                    latest_prices = PriceDataPoint(**price_dict)
                    logger.debug(f"Broadcasting price data: {price_dict}")
                
                await ws_manager.broadcast_all(
                    prices=latest_prices,
                    spread=spread_data,
                    correlation=correlation_data,
                    summary=summary_stats
                )
            
            # Always broadcast combined analytics (even with fallback values)
            if prices_dict:
                logger.debug(f"Broadcasting analytics: spread={spread}, z_score={z_score}, correlation={correlation}")
                await ws_manager.broadcast_analytics(
                    timestamp=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
                    prices=prices_dict,
                    spread=spread,
                    z_score=z_score,
                    correlation=correlation
                )
            
            # Wait exactly 1 second before next broadcast
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in analytics processor: {e}", exc_info=True)
            await asyncio.sleep(1)


async def tick_processor():
    """
    Background task that processes incoming ticks through the pipeline.
    """
    logger.info("Starting tick processor...")
    
    binance = get_binance_client()
    ingestion = get_ingestion_engine()
    resampling = get_resampling_engine()
    
    # Define tick handler
    def handle_tick(tick):
        """Synchronous tick handler that queues work."""
        asyncio.create_task(_process_tick(tick))
    
    async def _process_tick(tick):
        """Asynchronous tick processing."""
        try:
            # Ingest tick
            await ingestion.ingest_tick(tick)
            
            # Process directly (no need to get all history for minute bars)
            await resampling.process_ticks([tick], tick.symbol)
            
        except Exception as e:
            logger.error(f"Error processing tick: {e}", exc_info=True)
    
    # Subscribe to Binance ticks
    binance.subscribe_to_ticks(handle_tick)
    
    # This task just keeps the processor alive
    while True:
        await asyncio.sleep(60)


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Starts and stops background tasks.
    """
    logger.info("=" * 60)
    logger.info("Starting Real-Time Quantitative Analytics Backend")
    logger.info("=" * 60)
    
    # Initialize alert callback
    alerts = get_alert_manager()
    ws_manager = get_connection_manager()
    
    def on_alert(alert: Alert):
        """Broadcast alerts to frontend."""
        asyncio.create_task(ws_manager.broadcast_alert(alert))
    
    alerts.subscribe(on_alert)
    
    # Start Binance client
    binance = get_binance_client()
    binance_task = asyncio.create_task(binance.start())
    background_tasks.add(binance_task)
    
    # Start minute bar finalizer
    finalizer = get_minute_bar_finalizer()
    await finalizer.start()
    
    # Start processors
    tick_task = asyncio.create_task(tick_processor())
    analytics_task = asyncio.create_task(analytics_processor())
    background_tasks.add(tick_task)
    background_tasks.add(analytics_task)
    
    logger.info("✓ All background services started")
    logger.info(f"✓ Tracking symbols: {', '.join(settings.DEFAULT_SYMBOLS)}")
    logger.info(f"✓ Server running on {settings.API_HOST}:{settings.API_PORT}")
    logger.info("=" * 60)
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    await binance.stop()
    
    for task in background_tasks:
        task.cancel()
    
    await asyncio.gather(*background_tasks, return_exceptions=True)
    logger.info("✓ Shutdown complete")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Quantitative Market Analytics API",
    description="Real-time statistical arbitrage analytics engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REST Endpoints
# ============================================================================

@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "service": "Quantitative Market Analytics API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    binance = get_binance_client()
    ws_manager = get_connection_manager()
    ingestion = get_ingestion_engine()
    
    uptime = (datetime.utcnow() - app_start_time).total_seconds()
    
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        binanceConnected=binance.is_connected(),
        activeSymbols=ingestion.get_active_symbols(),
        frontendConnections=ws_manager.get_connection_count(),
        uptimeSeconds=uptime
    )


@app.post("/api/settings")
async def update_settings(settings_update: ControlSettings):
    """
    Update control panel settings.
    
    Args:
        settings_update: New control settings
        
    Returns:
        Confirmation message
    """
    global current_settings
    current_settings = settings_update
    
    logger.info(f"Settings updated: {settings_update.model_dump()}")
    
    # Update Binance client symbols if needed
    binance = get_binance_client()
    for symbol in settings_update.selectedSymbols:
        binance.add_symbol(symbol)
    
    return {
        "status": "success",
        "message": "Settings updated",
        "settings": settings_update.model_dump()
    }


@app.get("/api/alerts", response_model=List[Alert])
async def get_alerts(limit: int = 10):
    """
    Get recent alerts.
    
    Args:
        limit: Maximum number of alerts to return
        
    Returns:
        List of alerts
    """
    alerts = get_alert_manager()
    return await alerts.get_active_alerts(limit=limit)


@app.get("/api/export")
async def export_unified(
    format: str = "csv",
    interval: str = "1m",
    limit: int = 1000
):
    """
    Unified export endpoint that routes to appropriate format handler.
    
    Args:
        format: Export format (csv, json, parquet)
        interval: Timeframe interval
        limit: Number of records
        
    Returns:
        File download in requested format
    """
    symbol = current_settings.selectedSymbols[0] if current_settings.selectedSymbols else "BTCUSDT"
    
    if format == "csv":
        return await export_csv(symbol=symbol, limit=limit)
    elif format == "json":
        return await export_json(symbol=symbol, limit=limit)
    elif format == "parquet":
        return await export_parquet(symbol=symbol, limit=limit)
    else:
        return {"error": f"Unsupported format: {format}"}


@app.get("/export/csv")
async def export_csv(
    symbol: str = "BTCUSDT",
    limit: int = 100
):
    """
    Export data as CSV file.
    
    Args:
        symbol: Symbol to export
        limit: Number of records
        
    Returns:
        CSV file download
    """
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    resampling = get_resampling_engine()
    analytics = get_analytics_engine()
    
    # Get OHLCV bars
    bars = await resampling.get_bars(symbol, "1m", limit)
    
    if not bars:
        return {"error": "No data available"}
    
    # Get price history for analytics
    price_history = await resampling.get_price_history(
        symbols=[symbol, "ETHUSDT"],
        interval="1m",
        n=limit
    )
    
    # Compute analytics
    spread_data = None
    correlation_data = None
    
    if price_history and len(price_history) >= 2:
        spread_data = await analytics.compute_spread_analysis(
            price_history,
            threshold=2.0,
            regression_type="ols"
        )
        correlation_data = await analytics.compute_correlation(
            price_history,
            symbol_a=symbol,
            symbol_b="ETHUSDT"
        )
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "timestamp", "open", "high", "low", "close", "volume",
        "spread", "z_score", "correlation"
    ])
    
    # Write data rows
    for bar in bars:
        timestamp = bar["timestamp"].isoformat() if isinstance(bar["timestamp"], datetime) else str(bar["timestamp"])
        
        writer.writerow([
            timestamp,
            bar["open"],
            bar["high"],
            bar["low"],
            bar["close"],
            bar["volume"],
            spread_data.spread if spread_data else 0.0,
            spread_data.zScore if spread_data else 0.0,
            correlation_data.correlation if correlation_data else 0.0
        ])
    
    # Prepare response
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=market_data_{symbol}.csv"
        }
    )


@app.get("/export/json")
async def export_json(
    symbol: str = "BTCUSDT",
    limit: int = 50
):
    """
    Export data as JSON.
    
    Args:
        symbol: Symbol to export
        limit: Number of records
        
    Returns:
        JSON response with OHLCV + analytics
    """
    resampling = get_resampling_engine()
    analytics = get_analytics_engine()
    
    # Get OHLCV bars
    bars = await resampling.get_bars(symbol, "1m", limit)
    
    if not bars:
        return {"error": "No data available"}
    
    # Get price history for analytics
    price_history = await resampling.get_price_history(
        symbols=[symbol, "ETHUSDT"],
        interval="1m",
        n=limit
    )
    
    # Compute analytics
    spread_data = None
    correlation_data = None
    
    if price_history and len(price_history) >= 2:
        spread_data = await analytics.compute_spread_analysis(
            price_history,
            threshold=2.0,
            regression_type="ols"
        )
        correlation_data = await analytics.compute_correlation(
            price_history,
            symbol_a=symbol,
            symbol_b="ETHUSDT"
        )
    
    # Build records (flat structure)
    data = []
    for bar in bars:
        timestamp = bar["timestamp"].isoformat() if isinstance(bar["timestamp"], datetime) else str(bar["timestamp"])
        
        data.append({
            "timestamp": timestamp,
            "open": bar["open"],
            "high": bar["high"],
            "low": bar["low"],
            "close": bar["close"],
            "volume": bar["volume"],
            "spread": spread_data.spread if spread_data else 0.0,
            "z_score": spread_data.zScore if spread_data else 0.0,
            "correlation": correlation_data.correlation if correlation_data else 0.0
        })
    
    return {
        "symbol": symbol,
        "interval": "1m",
        "data": data
    }


@app.get("/export/parquet")
async def export_parquet(
    symbol: str = "BTCUSDT",
    limit: int = 1000
):
    """
    Export data as Parquet file.
    
    Args:
        symbol: Symbol to export
        limit: Number of records
        
    Returns:
        Parquet file download
    """
    from fastapi.responses import StreamingResponse
    import io
    
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        return {"error": "PyArrow not installed. Run: pip install pyarrow"}
    
    resampling = get_resampling_engine()
    analytics = get_analytics_engine()
    
    # Get OHLCV bars
    bars = await resampling.get_bars(symbol, "1m", limit)
    
    if not bars:
        return {"error": "No data available"}
    
    # Get price history for analytics
    price_history = await resampling.get_price_history(
        symbols=[symbol, "ETHUSDT"],
        interval="1m",
        n=limit
    )
    
    # Compute analytics
    spread_data = None
    correlation_data = None
    
    if price_history and len(price_history) >= 2:
        spread_data = await analytics.compute_spread_analysis(
            price_history,
            threshold=2.0,
            regression_type="ols"
        )
        correlation_data = await analytics.compute_correlation(
            price_history,
            symbol_a=symbol,
            symbol_b="ETHUSDT"
        )
    
    # Prepare data arrays
    timestamps = []
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []
    spreads = []
    z_scores = []
    correlations = []
    
    for bar in bars:
        timestamp = bar["timestamp"] if isinstance(bar["timestamp"], datetime) else datetime.fromisoformat(str(bar["timestamp"]))
        
        timestamps.append(timestamp)
        opens.append(bar["open"])
        highs.append(bar["high"])
        lows.append(bar["low"])
        closes.append(bar["close"])
        volumes.append(bar["volume"])
        spreads.append(spread_data.spread if spread_data else 0.0)
        z_scores.append(spread_data.zScore if spread_data else 0.0)
        correlations.append(correlation_data.correlation if correlation_data else 0.0)
    
    # Create PyArrow table
    table = pa.table({
        "timestamp": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "spread": spreads,
        "z_score": z_scores,
        "correlation": correlations
    })
    
    # Write to in-memory buffer
    output = io.BytesIO()
    pq.write_table(table, output)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename=market_analytics_{symbol}.parquet"
        }
    )


@app.get("/api/debug/bars")
async def debug_bars(symbol: str = "BTCUSDT", interval: str = "1m"):
    """Debug endpoint to check bar status."""
    resampling = get_resampling_engine()
    bars = await resampling.get_bars(symbol, interval, 60)
    
    return {
        "symbol": symbol,
        "interval": interval,
        "total_bars": len(bars),
        "complete_bars": len(resampling.minute_bars.get(symbol, [])),
        "has_incomplete": symbol in resampling.current_minute_bar,
        "bars": [
            {
                "timestamp": bar["timestamp"].isoformat() if isinstance(bar["timestamp"], datetime) else str(bar["timestamp"]),
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
                "volume": bar["volume"]
            }
            for bar in bars[-10:]  # Last 10 bars only
        ]
    }


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """WebSocket endpoint for price data stream."""
    ws_manager = get_connection_manager()
    await ws_manager.connect(websocket, "prices")
    
    try:
        while True:
            # Keep connection alive (actual data sent via broadcast)
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


@app.websocket("/ws/spread")
async def websocket_spread(websocket: WebSocket):
    """WebSocket endpoint for spread/z-score data stream."""
    ws_manager = get_connection_manager()
    await ws_manager.connect(websocket, "spread")
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


@app.websocket("/ws/correlation")
async def websocket_correlation(websocket: WebSocket):
    """WebSocket endpoint for correlation data stream."""
    ws_manager = get_connection_manager()
    await ws_manager.connect(websocket, "correlation")
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


@app.websocket("/ws/summary")
async def websocket_summary(websocket: WebSocket):
    """WebSocket endpoint for summary statistics stream."""
    ws_manager = get_connection_manager()
    await ws_manager.connect(websocket, "summary")
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for alert notifications."""
    ws_manager = get_connection_manager()
    await ws_manager.connect(websocket, "alerts")
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


@app.websocket("/ws/analytics")
async def websocket_analytics(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analytics stream.
    
    Sends combined analytics payload:
    {
        "timestamp": "2025-01-01T12:31:00",
        "prices": {"BTCUSDT": 67521.45, "ETHUSDT": 3456.78},
        "spread": 12.45,
        "z_score": -0.68,
        "correlation": 0.889
    }
    """
    ws_manager = get_connection_manager()
    await ws_manager.connect(websocket, "analytics")
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level="info"
    )
