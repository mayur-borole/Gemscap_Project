"""
Alert evaluation and notification system.
Monitors analytics for threshold breaches and generates alerts.
"""
import asyncio
import logging
from typing import List, Callable, Optional
from datetime import datetime, timedelta
from collections import deque
import uuid

from app.schemas import Alert, SpreadDataPoint, SummaryStats
from app.settings import settings

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages trading alerts based on quantitative thresholds.
    Implements cooldown logic to prevent alert spam.
    """
    
    def __init__(
        self,
        max_alerts: int = None,
        cooldown_seconds: int = None
    ):
        """
        Initialize alert manager.
        
        Args:
            max_alerts: Maximum alerts to keep in history
            cooldown_seconds: Minimum time between duplicate alerts
        """
        self.max_alerts = max_alerts or settings.MAX_ALERTS
        self.cooldown_seconds = cooldown_seconds or settings.ALERT_COOLDOWN_SECONDS
        
        self.alerts: deque[Alert] = deque(maxlen=self.max_alerts)
        self.last_alert_time: dict[str, datetime] = {}
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        self.lock = asyncio.Lock()
    
    def subscribe(self, callback: Callable[[Alert], None]):
        """
        Subscribe to alert notifications.
        
        Args:
            callback: Function to call when new alert is generated
        """
        self.alert_callbacks.append(callback)
        logger.info(f"Subscribed alert callback: {callback.__name__}")
    
    async def _should_fire_alert(self, alert_key: str) -> bool:
        """
        Check if enough time has passed since last alert of this type.
        
        Args:
            alert_key: Unique identifier for alert type
            
        Returns:
            True if alert should fire
        """
        now = datetime.utcnow()
        
        if alert_key not in self.last_alert_time:
            return True
        
        time_since_last = (now - self.last_alert_time[alert_key]).total_seconds()
        return time_since_last >= self.cooldown_seconds
    
    async def create_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        symbol: Optional[str] = None,
        value: Optional[float] = None,
        metric: Optional[str] = None,
        threshold: Optional[float] = None,
        direction: Optional[str] = None
    ) -> Optional[Alert]:
        """
        Create and register a new alert.
        
        Args:
            alert_type: 'info', 'warning', or 'danger'
            title: Alert title
            message: Alert message
            symbol: Related symbol (optional)
            value: Related numeric value (optional)
            
        Returns:
            Alert object if created, None if suppressed by cooldown
        """
        # Generate unique key for cooldown tracking
        alert_key = f"{alert_type}:{title}:{symbol}"
        
        if not await self._should_fire_alert(alert_key):
            return None
        
        async with self.lock:
            alert = Alert(
                id=str(uuid.uuid4()),
                type=alert_type,
                title=title,
                message=message,
                timestamp=datetime.utcnow().strftime('%H:%M:%S'),
                symbol=symbol,
                value=value,
                metric=metric,
                threshold=threshold,
                direction=direction
            )
            
            self.alerts.append(alert)
            self.last_alert_time[alert_key] = datetime.utcnow()
            
            logger.info(f"Alert: [{alert_type.upper()}] {title} - {message}")
            
            # Notify subscribers
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}", exc_info=True)
            
            return alert
    
    async def evaluate_zscore_alert(
        self,
        spread_data: SpreadDataPoint,
        threshold: float = 2.0
    ):
        """
        Evaluate z-score for threshold breach and generate alert if needed.
        
        Args:
            spread_data: Spread analysis results
            threshold: Z-score threshold
        """
        zscore = spread_data.zScore
        
        if abs(zscore) > threshold:
            alert_type = "ALERT"
            title = "Z-Score Threshold Breach"
            
            direction = "above" if zscore > 0 else "below"
            message = (
                f"Z-Score ({zscore:.2f}σ) is {direction} threshold (±{threshold}σ). "
                f"Mean reversion opportunity detected."
            )
            
            await self.create_alert(
                alert_type=alert_type,
                title=title,
                message=message,
                value=zscore,
                metric="z_score",
                threshold=threshold,
                direction=direction
            )
        elif abs(zscore) > threshold * 0.8:
            # Warning at 80% of threshold
            alert_type = "warning"
            title = "Z-Score Approaching Threshold"
            direction = "above" if zscore > 0 else "below"
            message = f"Z-Score ({zscore:.2f}σ) is approaching threshold (±{threshold}σ)."
            
            await self.create_alert(
                alert_type=alert_type,
                title=title,
                message=message,
                value=zscore,
                metric="z_score",
                threshold=threshold * 0.8,
                direction=direction
            )
    
    async def evaluate_correlation_alert(
        self,
        correlation: float,
        min_threshold: float = 0.5
    ):
        """
        Alert if correlation drops below expected level.
        
        Args:
            correlation: Correlation coefficient
            min_threshold: Minimum acceptable correlation
        """
        if abs(correlation) < min_threshold:
            await self.create_alert(
                alert_type="warning",
                title="Low Correlation Detected",
                message=(
                    f"Correlation ({correlation:.3f}) is below threshold ({min_threshold:.3f}). "
                    f"Spread strategy may be less reliable."
                ),
                value=correlation,
                metric="correlation",
                threshold=min_threshold,
                direction="below"
            )
    
    async def evaluate_volatility_alert(
        self,
        volatility: float,
        max_threshold: float = 1000.0
    ):
        """
        Alert if volatility spikes above normal levels.
        
        Args:
            volatility: Current volatility measure
            max_threshold: Maximum acceptable volatility
        """
        if volatility > max_threshold:
            await self.create_alert(
                alert_type="warning",
                title="High Volatility Alert",
                message=(
                    f"Rolling volatility ({volatility:.2f}) exceeds threshold ({max_threshold:.2f}). "
                    f"Exercise caution."
                ),
                value=volatility,
                metric="volatility",
                threshold=max_threshold,
                direction="above"
            )
    
    async def evaluate_summary_alerts(
        self,
        summary: SummaryStats,
        zscore_threshold: float = 2.0
    ):
        """
        Evaluate all alert conditions from summary statistics.
        
        Args:
            summary: Summary statistics object
            zscore_threshold: Z-score threshold
        """
        # Z-score alert
        if abs(summary.zScore) > zscore_threshold:
            spread_data = SpreadDataPoint(
                timestamp=int(datetime.utcnow().timestamp() * 1000),
                time=datetime.utcnow().strftime('%H:%M:%S'),
                spread=summary.spread,
                zScore=summary.zScore,
                upperThreshold=zscore_threshold,
                lowerThreshold=-zscore_threshold
            )
            await self.evaluate_zscore_alert(spread_data, zscore_threshold)
        
        # Correlation alert
        await self.evaluate_correlation_alert(summary.correlation, min_threshold=0.5)
        
        # Volatility alert
        await self.evaluate_volatility_alert(
            summary.rollingVolatility,
            max_threshold=500.0
        )
    
    async def get_active_alerts(self, limit: Optional[int] = None) -> List[Alert]:
        """
        Get recent alerts.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of Alert objects (newest first)
        """
        async with self.lock:
            alerts = list(self.alerts)
            alerts.reverse()  # Newest first
            if limit:
                alerts = alerts[:limit]
            return alerts
    
    async def clear_alerts(self):
        """Clear all alerts."""
        async with self.lock:
            self.alerts.clear()
            self.last_alert_time.clear()
            logger.info("Cleared all alerts")


# Global alert manager
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
