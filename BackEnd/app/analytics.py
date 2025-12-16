"""
Quantitative analytics engine for statistical arbitrage.
Computes spreads, z-scores, correlations, and regression-based metrics.
"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from statsmodels.tsa.stattools import adfuller

from app.schemas import (
    PriceDataPoint,
    SpreadDataPoint,
    CorrelationDataPoint,
    SummaryStats,
    MetricData,
)
from app.settings import settings

logger = logging.getLogger(__name__)


class SpreadAnalyzer:
    """
    Analyzes price spreads and computes z-scores for mean reversion trading.
    """
    
    def __init__(
        self,
        base_symbol: str = "BTCUSDT",
        hedge_symbol: str = "ETHUSDT",
        window: int = 20
    ):
        """
        Initialize spread analyzer.
        
        Args:
            base_symbol: Base asset symbol
            hedge_symbol: Hedge asset symbol
            window: Rolling window size for statistics
        """
        self.base_symbol = base_symbol
        self.hedge_symbol = hedge_symbol
        self.window = window
        self.spread_history: List[float] = []
    
    def compute_hedge_ratio(self, base_prices: List[float], hedge_prices: List[float]) -> float:
        """
        Compute hedge ratio using Ordinary Least Squares (OLS) regression.
        
        Mathematical formula:
            BTC_price = α + β * ETH_price + ε
        
        Where:
            β (beta) = hedge_ratio
            α (alpha) = intercept
            ε (epsilon) = residual error
        
        OLS minimizes: Σ(BTC_i - α - β*ETH_i)²
        
        Args:
            base_prices: Base asset prices (e.g., BTC)
            hedge_prices: Hedge asset prices (e.g., ETH)
            
        Returns:
            Hedge ratio (beta coefficient)
        """
        if len(base_prices) != len(hedge_prices) or len(base_prices) < 2:
            return 0.0
        
        # Convert to numpy arrays
        y = np.array(base_prices)  # Dependent variable (BTC)
        X = np.array(hedge_prices)  # Independent variable (ETH)
        
        # Add constant for intercept: X_with_const = [1, ETH_price]
        X_with_const = sm.add_constant(X)
        
        try:
            # Perform OLS regression
            # Model: y = X*β + ε
            # Solution: β = (X'X)^(-1) * X'y
            model = OLS(y, X_with_const).fit()
            
            # Extract hedge ratio (slope coefficient, β)
            hedge_ratio = model.params[1]
            
            logger.debug(f"OLS Regression: hedge_ratio={hedge_ratio:.4f}, R²={model.rsquared:.4f}")
            
            return float(hedge_ratio)
            
        except Exception as e:
            logger.error(f"OLS regression failed: {e}")
            return 0.0
    
    def compute_spread(
        self,
        base_prices: List[float],
        hedge_prices: List[float],
        regression_type: str = "ols"
    ) -> Tuple[List[float], float]:
        """
        Compute spread between two price series using regression.
        
        Mathematical formula:
            spread(t) = BTC_price(t) - hedge_ratio * ETH_price(t)
        
        This represents the deviation from the expected relationship.
        Mean reversion strategy: trade when spread deviates significantly.
        
        Args:
            base_prices: Base asset prices
            hedge_prices: Hedge asset prices
            regression_type: 'ols', 'robust', or 'ridge'
            
        Returns:
            Tuple of (spread_series, hedge_ratio)
        """
        if len(base_prices) != len(hedge_prices) or len(base_prices) < 2:
            return [], 0.0
        
        # Convert to numpy arrays
        y = np.array(base_prices)
        X = np.array(hedge_prices)
        
        # Add constant for intercept
        X_with_const = sm.add_constant(X)
        
        try:
            # Perform linear regression
            if regression_type == "robust":
                model = sm.RLM(y, X_with_const).fit()
            else:  # Default to OLS
                model = OLS(y, X_with_const).fit()
            
            hedge_ratio = model.params[1]  # Slope coefficient (β)
            
            # Compute spread: spread = BTC - β * ETH
            spread = y - hedge_ratio * X
            
            return spread.tolist(), float(hedge_ratio)
            
        except Exception as e:
            logger.error(f"Regression error: {e}")
            return [], 0.0
    
    def compute_zscore(self, spread: List[float]) -> Optional[float]:
        """
        Compute z-score of the latest spread value.
        
        Mathematical formula:
            z-score = (spread_current - μ) / σ
        
        Where:
            μ (mu) = mean of spread over rolling window
            σ (sigma) = standard deviation of spread over rolling window
        
        Interpretation:
            z-score > +2: Spread is 2 std devs above mean (overvalued, short signal)
            z-score < -2: Spread is 2 std devs below mean (undervalued, long signal)
            z-score ≈ 0: Spread is near mean (neutral)
        
        Args:
            spread: Spread time series
            
        Returns:
            Z-score of the most recent spread value
        """
        if len(spread) < self.window:
            return None
        
        # Use rolling window for mean and std calculation
        recent_spread = spread[-self.window:]
        
        # Calculate μ (mean)
        mean = np.mean(recent_spread)
        
        # Calculate σ (standard deviation) using Bessel's correction (ddof=1)
        std = np.std(recent_spread, ddof=1)
        
        if std == 0:
            return 0.0  # Avoid division by zero
        
        # Get latest spread value
        latest_spread = spread[-1]
        
        # Compute z-score: z = (x - μ) / σ
        zscore = (latest_spread - mean) / std
        
        return float(zscore)
    
    def analyze(
        self,
        base_prices: List[float],
        hedge_prices: List[float],
        threshold: float = 2.0,
        regression_type: str = "ols"
    ) -> Optional[SpreadDataPoint]:
        """
        Perform full spread analysis and return results.
        
        Args:
            base_prices: Base asset price history
            hedge_prices: Hedge asset price history
            threshold: Z-score threshold for alerts
            regression_type: Regression method
            
        Returns:
            SpreadDataPoint or None if insufficient data
        """
        if len(base_prices) < self.window or len(hedge_prices) < self.window:
            return None
        
        # Compute spread
        spread_series, hedge_ratio = self.compute_spread(
            base_prices, hedge_prices, regression_type
        )
        
        if not spread_series:
            return None
        
        # Compute z-score
        zscore = self.compute_zscore(spread_series)
        
        if zscore is None:
            return None
        
        # Create data point
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        time_str = datetime.utcnow().strftime('%H:%M:%S')
        
        return SpreadDataPoint(
            timestamp=timestamp,
            time=time_str,
            spread=float(spread_series[-1]),
            zScore=float(zscore),
            upperThreshold=threshold,
            lowerThreshold=-threshold
        )


class CorrelationAnalyzer:
    """
    Computes rolling correlation between two asset price series.
    """
    
    def __init__(self, window: int = 60):
        """
        Initialize correlation analyzer.
        
        Args:
            window: Rolling window size
        """
        self.window = window
    
    def compute_correlation(
        self,
        prices_a: List[float],
        prices_b: List[float]
    ) -> Optional[float]:
        """
        Compute Pearson correlation coefficient (rolling window).
        
        Mathematical formula:
            ρ(X,Y) = Cov(X,Y) / (σ_X * σ_Y)
        
        Or equivalently:
            ρ = Σ[(X_i - X̄)(Y_i - Ȳ)] / √[Σ(X_i - X̄)² * Σ(Y_i - Ȳ)²]
        
        Where:
            ρ (rho) = correlation coefficient
            Cov(X,Y) = covariance between X and Y
            σ_X, σ_Y = standard deviations
            X̄, Ȳ = means
        
        Range: -1 ≤ ρ ≤ +1
            ρ = +1: Perfect positive correlation
            ρ = 0: No linear correlation
            ρ = -1: Perfect negative correlation
        
        Args:
            prices_a: First price series
            prices_b: Second price series
            
        Returns:
            Correlation coefficient or None if insufficient data
        """
        if len(prices_a) < self.window or len(prices_b) < self.window:
            return None
        
        # Use latest rolling window
        a = np.array(prices_a[-self.window:])
        b = np.array(prices_b[-self.window:])
        
        # Compute Pearson correlation coefficient
        # scipy.stats.pearsonr returns (correlation, p-value)
        correlation, p_value = stats.pearsonr(a, b)
        
        logger.debug(f"Correlation: ρ={correlation:.4f}, p-value={p_value:.4f}")
        
        return float(correlation)
    
    def analyze(
        self,
        prices_a: List[float],
        prices_b: List[float]
    ) -> Optional[CorrelationDataPoint]:
        """
        Analyze correlation and return data point.
        
        Args:
            prices_a: First price series
            prices_b: Second price series
            
        Returns:
            CorrelationDataPoint or None
        """
        correlation = self.compute_correlation(prices_a, prices_b)
        
        if correlation is None:
            return None
        
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        time_str = datetime.utcnow().strftime('%H:%M:%S')
        
        return CorrelationDataPoint(
            timestamp=timestamp,
            time=time_str,
            correlation=correlation
        )


class StationarityTester:
    """
    Tests time series for stationarity using Augmented Dickey-Fuller test.
    """
    
    @staticmethod
    def adf_test(spread: List[float], significance_level: float = 0.05) -> dict:
        """
        Perform Augmented Dickey-Fuller test for stationarity.
        
        Mathematical concept:
            Tests the null hypothesis: H0: Time series has a unit root (non-stationary)
        
        ADF test equation:
            \u0394y_t = \u03b1 + \u03b2*t + \u03b3*y_(t-1) + \u03b4_1*\u0394y_(t-1) + ... + \u03b4_p*\u0394y_(t-p) + \u03b5_t
        
        Where:
            \u0394y_t = first difference (y_t - y_(t-1))
            \u03b3 = coefficient being tested (\u03b3 < 0 means stationary)
            p = number of lags
        
        Interpretation:
            - If p-value < 0.05: Reject H0 \u2192 Series is STATIONARY (good for pairs trading)
            - If p-value \u2265 0.05: Fail to reject H0 \u2192 Series is NON-STATIONARY
        
        Stationary spread = Mean reversion property = Profitable pairs trading
        
        Args:
            spread: Spread time series
            significance_level: Critical p-value (default 0.05 = 95% confidence)
            
        Returns:
            Dictionary with ADF test results
        """
        if len(spread) < 12:  # Minimum for ADF test
            return {
                "adf_statistic": 0.0,
                "p_value": 1.0,
                "stationary": False,
                "critical_values": {},
                "error": "Insufficient data for ADF test (need ≥12 points)"
            }
        
        try:
            # Perform Augmented Dickey-Fuller test
            # Returns: (adf_stat, p_value, lags_used, nobs, critical_values, icbest)
            result = adfuller(spread, autolag='AIC')
            
            adf_statistic = result[0]
            p_value = result[1]
            critical_values = result[4]  # Dict: {'1%': ..., '5%': ..., '10%': ...}
            
            # Determine stationarity
            # Stationary if: p-value < significance_level OR adf_stat < critical_value
            is_stationary = p_value < significance_level
            
            logger.debug(
                f"ADF Test: statistic={adf_statistic:.4f}, "
                f"p-value={p_value:.4f}, stationary={is_stationary}"
            )
            
            return {
                "adf_statistic": float(adf_statistic),
                "p_value": float(p_value),
                "stationary": bool(is_stationary),
                "critical_values": {
                    "1%": float(critical_values['1%']),
                    "5%": float(critical_values['5%']),
                    "10%": float(critical_values['10%'])
                },
                "interpretation": (
                    "Spread is STATIONARY (mean-reverting)" if is_stationary 
                    else "Spread is NON-STATIONARY (trending)"
                )
            }
            
        except Exception as e:
            logger.error(f"ADF test failed: {e}")
            return {
                "adf_statistic": 0.0,
                "p_value": 1.0,
                "stationary": False,
                "critical_values": {},
                "error": str(e)
            }


class StatisticsCalculator:
    """Computes rolling statistical metrics (mean, volatility, etc.)."""
    
    @staticmethod
    def rolling_mean(prices: List[float], window: int) -> Optional[float]:
        """Compute rolling mean."""
        if len(prices) < window:
            return None
        return float(np.mean(prices[-window:]))
    
    @staticmethod
    def rolling_std(prices: List[float], window: int) -> Optional[float]:
        """Compute rolling standard deviation."""
        if len(prices) < window:
            return None
        return float(np.std(prices[-window:], ddof=1))
    
    @staticmethod
    def price_change(current: float, previous: float) -> Tuple[float, float]:
        """
        Compute absolute and percentage price change.
        
        Returns:
            Tuple of (absolute_change, percentage_change)
        """
        change = current - previous
        change_pct = (change / previous * 100) if previous != 0 else 0.0
        return float(change), float(change_pct)


class AnalyticsEngine:
    """
    Orchestrates all quantitative analytics computations.
    """
    
    def __init__(self):
        """Initialize analytics engine."""
        self.spread_analyzer = SpreadAnalyzer(
            base_symbol=settings.BASE_SYMBOL,
            hedge_symbol=settings.HEDGE_SYMBOL,
            window=settings.ROLLING_WINDOW
        )
        self.correlation_analyzer = CorrelationAnalyzer(
            window=settings.CORRELATION_WINDOW
        )
        self.stationarity_tester = StationarityTester()
        self.stats_calculator = StatisticsCalculator()
        logger.info("Analytics engine initialized")
    
    async def compute_spread_analysis(
        self,
        price_history: List[PriceDataPoint],
        threshold: float = 2.0,
        regression_type: str = "ols"
    ) -> Optional[SpreadDataPoint]:
        """
        Compute spread analysis from price history.
        
        Args:
            price_history: Historical price data
            threshold: Z-score threshold
            regression_type: Regression method
            
        Returns:
            SpreadDataPoint or None
        """
        if not price_history:
            return None
        
        # Extract price series (handle both dict and object)
        base_prices = []
        hedge_prices = []
        for p in price_history:
            if isinstance(p, dict):
                base_price = p.get(self.spread_analyzer.base_symbol)
                hedge_price = p.get(self.spread_analyzer.hedge_symbol)
            else:
                base_price = getattr(p, self.spread_analyzer.base_symbol, None)
                hedge_price = getattr(p, self.spread_analyzer.hedge_symbol, None)
            
            if base_price is not None:
                base_prices.append(base_price)
            if hedge_price is not None:
                hedge_prices.append(hedge_price)
        
        if not base_prices or not hedge_prices:
            return None
        
        return self.spread_analyzer.analyze(
            base_prices, hedge_prices, threshold, regression_type
        )
    
    async def compute_correlation(
        self,
        price_history: List[PriceDataPoint],
        symbol_a: str = "BTCUSDT",
        symbol_b: str = "ETHUSDT"
    ) -> Optional[CorrelationDataPoint]:
        """
        Compute correlation from price history.
        
        Args:
            price_history: Historical price data
            symbol_a: First symbol
            symbol_b: Second symbol
            
        Returns:
            CorrelationDataPoint or None
        """
        if not price_history:
            return None
        
        # Extract prices (handle both dict and object)
        prices_a = []
        prices_b = []
        for p in price_history:
            if isinstance(p, dict):
                price_a = p.get(symbol_a)
                price_b = p.get(symbol_b)
            else:
                price_a = getattr(p, symbol_a, None)
                price_b = getattr(p, symbol_b, None)
            
            if price_a is not None:
                prices_a.append(price_a)
            if price_b is not None:
                prices_b.append(price_b)
        
        if not prices_a or not prices_b:
            return None
        
        return self.correlation_analyzer.analyze(prices_a, prices_b)
    
    async def compute_summary_stats(
        self,
        price_history: List[PriceDataPoint],
        symbols: List[str],
        window: int = 20
    ) -> Optional[SummaryStats]:
        """
        Compute comprehensive summary statistics.
        
        Args:
            price_history: Historical price data
            symbols: List of symbols to analyze
            window: Rolling window size
            
        Returns:
            SummaryStats object or None
        """
        if not price_history or len(price_history) < 2:
            return None
        
        # Latest and previous prices for each symbol
        latest_metrics = []
        
        for symbol in symbols:
            # Extract prices (handle both dict and object)
            prices = []
            for p in price_history:
                if isinstance(p, dict):
                    price = p.get(symbol)
                else:
                    price = getattr(p, symbol, None)
                if price is not None:
                    prices.append(price)
            prices = [p for p in prices if p is not None]
            
            if len(prices) >= 2:
                current_price = prices[-1]
                previous_price = prices[-2]
                change, change_pct = self.stats_calculator.price_change(
                    current_price, previous_price
                )
                
                latest_metrics.append(MetricData(
                    symbol=symbol,
                    price=current_price,
                    change=change,
                    changePercent=change_pct
                ))
        
        # Compute spread and z-score
        spread_data = await self.compute_spread_analysis(price_history)
        spread_value = spread_data.spread if spread_data else 0.0
        zscore_value = spread_data.zScore if spread_data else 0.0
        
        # Compute correlation
        corr_data = await self.compute_correlation(price_history)
        correlation_value = corr_data.correlation if corr_data else 0.0
        
        # Rolling statistics for base symbol
        base_prices = [
            getattr(p, self.spread_analyzer.base_symbol, None)
            for p in price_history
        ]
        base_prices = [p for p in base_prices if p is not None]
        
        rolling_mean = self.stats_calculator.rolling_mean(base_prices, window) or 0.0
        rolling_vol = self.stats_calculator.rolling_std(base_prices, window) or 0.0
        
        return SummaryStats(
            latestPrices=latest_metrics,
            spread=spread_value,
            zScore=zscore_value,
            rollingMean=rolling_mean,
            rollingVolatility=rolling_vol,
            correlation=correlation_value
        )


# Global analytics engine
_analytics_engine: Optional[AnalyticsEngine] = None


def get_analytics_engine() -> AnalyticsEngine:
    """Get or create the global analytics engine instance."""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine
