// Mock data generator for trading dashboard
// This will be replaced by Python backend data later

export interface PriceDataPoint {
  timestamp: number;
  time: string;
  BTCUSDT: number;
  ETHUSDT: number;
  SOLUSDT: number;
}

export interface SpreadDataPoint {
  timestamp: number;
  time: string;
  spread: number;
  zScore: number;
  upperThreshold: number;
  lowerThreshold: number;
}

export interface CorrelationDataPoint {
  timestamp: number;
  time: string;
  correlation: number;
}

export interface MetricData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
}

// Generate realistic price data
export const generatePriceData = (points: number = 60): PriceDataPoint[] => {
  const data: PriceDataPoint[] = [];
  const now = Date.now();
  const interval = 60000; // 1 minute

  let btcPrice = 67500;
  let ethPrice = 3450;
  let solPrice = 145;

  for (let i = points; i >= 0; i--) {
    const timestamp = now - i * interval;
    const time = new Date(timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });

    // Random walk with trend
    btcPrice += (Math.random() - 0.48) * 150;
    ethPrice += (Math.random() - 0.48) * 15;
    solPrice += (Math.random() - 0.48) * 2;

    data.push({
      timestamp,
      time,
      BTCUSDT: Math.round(btcPrice * 100) / 100,
      ETHUSDT: Math.round(ethPrice * 100) / 100,
      SOLUSDT: Math.round(solPrice * 100) / 100,
    });
  }

  return data;
};

// Generate spread and z-score data
export const generateSpreadData = (points: number = 60, threshold: number = 2): SpreadDataPoint[] => {
  const data: SpreadDataPoint[] = [];
  const now = Date.now();
  const interval = 60000;

  let spread = 0;
  const mean = 0;
  const std = 50;

  for (let i = points; i >= 0; i--) {
    const timestamp = now - i * interval;
    const time = new Date(timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });

    // Mean-reverting spread
    spread = spread * 0.95 + (Math.random() - 0.5) * 40;
    const zScore = spread / std;

    data.push({
      timestamp,
      time,
      spread: Math.round(spread * 100) / 100,
      zScore: Math.round(zScore * 100) / 100,
      upperThreshold: threshold,
      lowerThreshold: -threshold,
    });
  }

  return data;
};

// Generate correlation data
export const generateCorrelationData = (points: number = 60): CorrelationDataPoint[] => {
  const data: CorrelationDataPoint[] = [];
  const now = Date.now();
  const interval = 60000;

  let correlation = 0.85;

  for (let i = points; i >= 0; i--) {
    const timestamp = now - i * interval;
    const time = new Date(timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });

    // Slowly varying correlation
    correlation = Math.max(-1, Math.min(1, correlation + (Math.random() - 0.5) * 0.05));

    data.push({
      timestamp,
      time,
      correlation: Math.round(correlation * 1000) / 1000,
    });
  }

  return data;
};

// Summary statistics
export interface SummaryStats {
  latestPrices: MetricData[];
  spread: number;
  zScore: number;
  rollingMean: number;
  rollingVolatility: number;
  correlation: number;
}

export const generateSummaryStats = (): SummaryStats => {
  return {
    latestPrices: [
      { symbol: 'BTCUSDT', price: 67523.45, change: 234.56, changePercent: 0.35 },
      { symbol: 'ETHUSDT', price: 3456.78, change: -12.34, changePercent: -0.36 },
      { symbol: 'SOLUSDT', price: 145.67, change: 2.89, changePercent: 2.02 },
    ],
    spread: 12.45,
    zScore: 1.23,
    rollingMean: 67450.12,
    rollingVolatility: 234.56,
    correlation: 0.876,
  };
};

// Available symbols
export const AVAILABLE_SYMBOLS = [
  { value: 'BTCUSDT', label: 'BTC/USDT' },
  { value: 'ETHUSDT', label: 'ETH/USDT' },
  { value: 'SOLUSDT', label: 'SOL/USDT' },
  { value: 'BNBUSDT', label: 'BNB/USDT' },
  { value: 'XRPUSDT', label: 'XRP/USDT' },
  { value: 'ADAUSDT', label: 'ADA/USDT' },
];

// Timeframe options
export const TIMEFRAMES = [
  { value: '1s', label: '1 Second' },
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '1h', label: '1 Hour' },
];

// Regression types
export const REGRESSION_TYPES = [
  { value: 'ols', label: 'OLS (Ordinary Least Squares)' },
  { value: 'robust', label: 'Robust Regression' },
  { value: 'ridge', label: 'Ridge Regression' },
];
