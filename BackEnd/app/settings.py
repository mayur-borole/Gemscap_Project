"""
Configuration settings for the quantitative analytics backend.
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:8083",
        "http://localhost:5173",
        "http://localhost:3000",
        "https://gemscap-project-u117.vercel.app",
        "https://gemscap-project-7waq.vercel.app",
        "https://*.vercel.app",
    ]
    
    # Binance Configuration
    BINANCE_WS_URL: str = "wss://fstream.binance.com/stream"  # Binance Futures
    DEFAULT_SYMBOLS: List[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    # Trading Pair Configuration
    BASE_SYMBOL: str = "BTCUSDT"  # For spread calculation
    HEDGE_SYMBOL: str = "ETHUSDT"  # For spread calculation
    
    # Timeframe Configuration
    TICK_BUFFER_SIZE: int = 10000  # Maximum ticks to buffer per symbol
    RESAMPLE_INTERVALS: List[str] = ["1s", "1m", "5m", "15m", "1h"]
    DEFAULT_INTERVAL: str = "1m"
    
    # Analytics Configuration
    ROLLING_WINDOW: int = 20  # Default window for rolling statistics
    Z_SCORE_THRESHOLD: float = 2.0  # Default z-score alert threshold
    CORRELATION_WINDOW: int = 60  # Window for correlation calculation
    
    # Alert Configuration
    ALERT_COOLDOWN_SECONDS: int = 60  # Minimum time between same alerts
    MAX_ALERTS: int = 100  # Maximum alerts to keep in memory
    
    # Data Export Configuration
    EXPORT_MAX_ROWS: int = 100000  # Maximum rows for CSV/JSON export
    EXPORT_DIR: str = "./exports"  # Directory for export files
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30  # Seconds between heartbeat pings
    WS_MAX_CONNECTIONS: int = 100  # Maximum concurrent frontend connections
    BATCH_PUBLISH_INTERVAL: int = 1  # Seconds between analytics updates
    
    # Performance Configuration
    BATCH_PUBLISH_INTERVAL: float = 1.0  # Seconds between frontend updates
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
