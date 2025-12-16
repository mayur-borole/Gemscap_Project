/**
 * API Service - Connects to Python Backend (FastAPI)
 * Implements all GEMSCAP 9-step requirements
 */

// Backend URLs from environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
const WS_ANALYTICS_URL = `${WS_BASE_URL}/ws/analytics`;

// ============================================================================
// REST API Endpoints
// ============================================================================

/**
 * Check backend health (Step 1-2: Verify connection to Binance data)
 */
export const checkHealth = async () => {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) throw new Error('Backend health check failed');
  return response.json();
};

/**
 * Update control settings (Steps 3-5: Configure resampling, spread, correlation)
 */
export const updateSettings = async (settings: {
  selectedSymbols: string[];
  timeframe: string;
  windowSize: number;
  regressionType: string;
  zScoreThreshold: number;
  correlationThreshold?: number;
  volatilityThreshold?: number;
}) => {
  const response = await fetch(`${API_BASE_URL}/api/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  if (!response.ok) throw new Error('Failed to update settings');
  return response.json();
};

/**
 * Get alerts history (Step 7: Alert system)
 */
export const getAlerts = async () => {
  const response = await fetch(`${API_BASE_URL}/api/alerts`);
  if (!response.ok) throw new Error('Failed to fetch alerts');
  return response.json();
};

/**
 * Export data (Step 8: Multi-format export)
 */
export const exportData = async (
  format: 'csv' | 'json' | 'parquet',
  interval: string = '1m',
  limit: number = 1000
) => {
  const params = new URLSearchParams({ format, interval, limit: limit.toString() });
  const response = await fetch(`${API_BASE_URL}/api/export?${params}`);
  if (!response.ok) throw new Error('Failed to export data');
  
  // Handle binary formats
  if (format === 'parquet') {
    return response.blob();
  }
  
  // Handle text formats
  return response.text();
};

// ============================================================================
// WebSocket Connections (Step 6: Real-time streaming)
// ============================================================================

export interface PriceUpdate {
  timestamp: number;
  [symbol: string]: number; // Dynamic symbol keys
}

export interface SpreadUpdate {
  timestamp: number;
  spread: number;
  zScore: number;
  upperThreshold: number;
  lowerThreshold: number;
  coefficients?: { slope: number; intercept: number };
}

export interface CorrelationUpdate {
  timestamp: number;
  correlation: number;
  symbol_a: string;
  symbol_b: string;
}

export interface SummaryUpdate {
  timestamp: number;
  symbols: Array<{
    symbol: string;
    price: number;
    change_1m: number;
    change_pct_1m: number;
  }>;
  spread?: {
    current: number;
    mean: number;
    std: number;
  };
  correlation?: number;
}

export interface AlertUpdate {
  id: string;
  type: 'z_score' | 'correlation' | 'volatility';
  severity: 'info' | 'warning' | 'danger';
  message: string;
  timestamp: string;
  data: Record<string, any>;
}

export interface AnalyticsUpdate {
  timestamp: string;
  prices: Record<string, number>;
  spread: number;
  z_score: number;
  correlation: number;
}

/**
 * Create a WebSocket connection with automatic reconnection
 */
class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 2000;
  private messageHandler: ((data: any) => void) | null = null;
  private errorHandler: ((error: Event) => void) | null = null;
  private closeHandler: (() => void) | null = null;
  private isManualClose = false;

  constructor(endpoint: string) {
    this.url = `${WS_BASE_URL}${endpoint}`;
    console.log(`🔗 WebSocket URL configured: ${this.url}`);
  }

  connect(
    onMessage: (data: any) => void,
    onError?: (error: Event) => void,
    onClose?: () => void
  ) {
    this.messageHandler = onMessage;
    this.errorHandler = onError || null;
    this.closeHandler = onClose || null;
    this.isManualClose = false;
    this._connect();
  }

  private _connect() {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log(`WebSocket connected: ${this.url}`);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          // Backend wraps data in { type, data, timestamp } structure
          // Extract the inner 'data' field if present
          const data = message.data || message;
          if (this.messageHandler) {
            this.messageHandler(data);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error(`WebSocket error: ${this.url}`, error);
        if (this.errorHandler) {
          this.errorHandler(error);
        }
      };

      this.ws.onclose = () => {
        console.log(`WebSocket closed: ${this.url}`);
        
        if (this.closeHandler) {
          this.closeHandler();
        }

        // Attempt reconnection if not manually closed
        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(
            `Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
          );
          setTimeout(() => this._connect(), this.reconnectDelay);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }

  close() {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

// ============================================================================
// WebSocket Endpoint Factories
// ============================================================================

/**
 * Connect to live price updates (Step 1-2: Real-time Binance data)
 */
export const connectPrices = (onMessage: (data: PriceUpdate) => void) => {
  const client = new WebSocketClient('/ws/prices');
  client.connect(onMessage);
  return client;
};

/**
 * Connect to spread & z-score updates (Step 4: Spread computation)
 */
export const connectSpread = (onMessage: (data: SpreadUpdate) => void) => {
  const client = new WebSocketClient('/ws/spread');
  client.connect(onMessage);
  return client;
};

/**
 * Connect to correlation updates (Step 5: Rolling correlation)
 */
export const connectCorrelation = (onMessage: (data: CorrelationUpdate) => void) => {
  const client = new WebSocketClient('/ws/correlation');
  client.connect(onMessage);
  return client;
};

/**
 * Connect to summary statistics (Steps 1-5: Combined metrics)
 */
export const connectSummary = (onMessage: (data: SummaryUpdate) => void) => {
  const client = new WebSocketClient('/ws/summary');
  client.connect(onMessage);
  return client;
};

/**
 * Connect to alert notifications (Step 7: Alert system)
 */
export const connectAlerts = (onMessage: (data: AlertUpdate) => void) => {
  const client = new WebSocketClient('/ws/alerts');
  client.connect(onMessage);
  return client;
};

/**
 * Connect to unified analytics stream (All metrics combined)
 */
export const connectAnalytics = (onMessage: (data: AnalyticsUpdate) => void) => {
  const client = new WebSocketClient('/ws/analytics');
  client.connect(onMessage);
  return client;
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Download exported data as file
 */
export const downloadExportedData = (data: string | Blob, filename: string) => {
  const blob = typeof data === 'string' ? new Blob([data], { type: 'text/plain' }) : data;
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
