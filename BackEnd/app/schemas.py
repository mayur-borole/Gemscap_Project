"""
Pydantic schemas for data validation and serialization.
These models match the frontend TypeScript interfaces.
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Price Data Models
# ============================================================================

class TickData(BaseModel):
    """Raw tick data from Binance."""
    symbol: str
    price: float
    timestamp: str  # ISO 8601 timestamp (e.g., "2025-01-01T12:30:00.123Z")
    qty: float


class PriceDataPoint(BaseModel):
    """Price data point for multiple symbols (matches frontend)."""
    timestamp: int
    time: str  # Formatted time string (HH:MM:SS)
    BTCUSDT: Optional[float] = None
    ETHUSDT: Optional[float] = None
    SOLUSDT: Optional[float] = None
    
    class Config:
        extra = "allow"  # Allow additional symbol fields dynamically


class OHLCVBar(BaseModel):
    """OHLCV candlestick bar."""
    timestamp: str  # ISO 8601 format (e.g., "2025-01-01T12:31:00")
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str


# ============================================================================
# Spread & Z-Score Models
# ============================================================================

class SpreadDataPoint(BaseModel):
    """Spread and z-score data (matches frontend)."""
    timestamp: int
    time: str
    spread: float
    zScore: float
    upperThreshold: float = 2.0
    lowerThreshold: float = -2.0


# ============================================================================
# Correlation Models
# ============================================================================

class CorrelationDataPoint(BaseModel):
    """Rolling correlation data (matches frontend)."""
    timestamp: int
    time: str
    correlation: float


# ============================================================================
# Summary Statistics Models
# ============================================================================

class MetricData(BaseModel):
    """Individual metric for a symbol."""
    symbol: str
    price: float
    change: float
    changePercent: float


class SummaryStats(BaseModel):
    """Summary statistics (matches frontend)."""
    latestPrices: List[MetricData]
    spread: float
    zScore: float
    rollingMean: float
    rollingVolatility: float
    correlation: float


# ============================================================================
# Alert Models
# ============================================================================

class Alert(BaseModel):
    """Trading alert."""
    id: str
    type: str = Field(..., pattern="^(info|warning|danger|ALERT)$")
    title: str
    message: str
    timestamp: str
    symbol: Optional[str] = None
    value: Optional[float] = None
    metric: Optional[str] = None  # e.g., "z_score", "correlation", "volatility"
    threshold: Optional[float] = None  # Threshold that was breached
    direction: Optional[str] = None  # "above", "below", "outside"


# ============================================================================
# Control Panel Settings Models
# ============================================================================

class ControlSettings(BaseModel):
    """Control panel settings from frontend."""
    selectedSymbols: List[str] = ["BTCUSDT", "ETHUSDT"]
    timeframe: str = "1m"
    windowSize: int = 20
    regressionType: str = "ols"
    zScoreThreshold: float = 2.0
    isLive: bool = True


# ============================================================================
# Export Models
# ============================================================================

class ExportRequest(BaseModel):
    """Data export request."""
    format: str = Field(..., pattern="^(csv|json|parquet)$")
    startTime: Optional[int] = None
    endTime: Optional[int] = None
    symbols: Optional[List[str]] = None


class ExportResponse(BaseModel):
    """Export response."""
    filename: str
    url: str
    rowCount: int
    format: str


# ============================================================================
# WebSocket Message Models
# ============================================================================

class WSMessage(BaseModel):
    """Generic WebSocket message."""
    type: str  # "prices", "spread", "correlation", "summary", "alert"
    data: Dict
    timestamp: int


# ============================================================================
# Health Check Models
# ============================================================================

class HealthCheck(BaseModel):
    """API health check response."""
    status: str
    timestamp: str
    binanceConnected: bool
    activeSymbols: List[str]
    frontendConnections: int
    uptimeSeconds: float
