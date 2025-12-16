import { useEffect, useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { ControlPanel, ControlSettings } from '@/components/dashboard/ControlPanel';
import { PriceChart } from '@/components/dashboard/PriceChart';
import { SpreadZScoreChart } from '@/components/dashboard/SpreadZScoreChart';
import { CorrelationChart } from '@/components/dashboard/CorrelationChart';
import { SummaryStats } from '@/components/dashboard/SummaryStats';
import { AlertsPanel } from '@/components/dashboard/AlertsPanel';
import { ExportPanel } from '@/components/dashboard/ExportPanel';
import { useToast } from '@/hooks/use-toast';
import {
  connectPrices,
  connectSpread,
  connectCorrelation,
  connectSummary,
  connectAlerts,
  connectAnalytics,
  updateSettings,
  checkHealth,
  type PriceUpdate,
  type SpreadUpdate,
  type CorrelationUpdate,
  type SummaryUpdate,
  type AlertUpdate,
  type AnalyticsUpdate,
} from '@/services/api';

interface PriceDataPoint {
  timestamp: number;
  time: string;
  [key: string]: number | string;
}

interface SpreadDataPoint {
  timestamp: number;
  time: string;
  spread: number;
  zScore: number;
  upperThreshold: number;
  lowerThreshold: number;
}

interface CorrelationDataPoint {
  timestamp: number;
  time: string;
  correlation: number;
}

const Index = () => {
  const { toast } = useToast();
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['BTCUSDT', 'ETHUSDT']);
  const [displaySymbols] = useState<string[]>(['BTCUSDT', 'ETHUSDT', 'SOLUSDT']); // For price chart display
  const [zScoreThreshold, setZScoreThreshold] = useState(2);
  const [correlationThreshold, setCorrelationThreshold] = useState(0.5);
  const [volatilityThreshold, setVolatilityThreshold] = useState(1000);
  
  // Real-time data from backend
  const [priceData, setPriceData] = useState<PriceDataPoint[]>([]);
  const [spreadData, setSpreadData] = useState<SpreadDataPoint[]>([]);
  const [correlationData, setCorrelationData] = useState<CorrelationDataPoint[]>([]);
  const [summaryStats, setSummaryStats] = useState<any>({ latestPrices: [] });
  const [alerts, setAlerts] = useState<AlertUpdate[]>([]);

  // Remove alert by index
  const removeAlert = (index: number) => {
    setAlerts(prev => prev.filter((_, i) => i !== index));
  };

  // Check backend health on mount
  useEffect(() => {
    checkHealth()
      .then(async () => {
        setIsBackendConnected(true);
        
        // Send initial settings to backend with all display symbols for streaming
        await updateSettings({
          selectedSymbols: displaySymbols, // Send all 3 for price data streaming
          timeframe: '1m',
          windowSize: 20,
          regressionType: 'ols',
          zScoreThreshold: zScoreThreshold,
          correlationThreshold: correlationThreshold,
          volatilityThreshold: volatilityThreshold,
        });
        console.log('✅ Initial settings sent to backend:', displaySymbols);
        
        toast({
          title: '✅ Backend Connected',
          description: 'Successfully connected to Python backend on port 8000',
        });
      })
      .catch((error) => {
        console.error('Backend connection failed:', error);
        toast({
          title: '❌ Backend Not Available',
          description: 'Make sure backend is running: python run.py',
          variant: 'destructive',
        });
      });
  }, []);

  // Connect to WebSocket streams
  useEffect(() => {
    if (!isBackendConnected) {
      console.log('⏸️ WebSocket connections waiting for backend health check...');
      return;
    }

    console.log('🔌 Starting WebSocket connections...');

    // Connect to prices WebSocket
    const pricesWs = connectPrices((data: PriceUpdate) => {
      console.log('📊 Received price data:', data);
      const newPoint: PriceDataPoint = {
        timestamp: data.timestamp,
        time: new Date(data.timestamp * 1000).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }),
      };
      
      // Add all symbol prices dynamically from WebSocket payload
      Object.keys(data).forEach((key) => {
        if (key !== 'timestamp') {
          newPoint[key] = data[key];
        }
      });

      setPriceData((prev) => {
        const updated = [...prev, newPoint];
        // Maintain rolling window: 60 points = last 60 seconds of data
        // Adjust maxPoints based on timeframe: 1m=60, 5m=300, 15m=900
        const maxPoints = 60;
        return updated.slice(-maxPoints);
      });
    });

    // Connect to spread WebSocket
    const spreadWs = connectSpread((data: SpreadUpdate) => {
      const newPoint: SpreadDataPoint = {
        timestamp: data.timestamp,
        time: new Date(data.timestamp * 1000).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }),
        spread: data.spread,
        zScore: data.zScore,
        upperThreshold: data.upperThreshold,
        lowerThreshold: data.lowerThreshold,
      };

      setSpreadData((prev) => {
        const updated = [...prev, newPoint];
        return updated.slice(-60);
      });
    });

    // Connect to correlation WebSocket
    const correlationWs = connectCorrelation((data: CorrelationUpdate) => {
      const newPoint: CorrelationDataPoint = {
        timestamp: data.timestamp,
        time: new Date(data.timestamp * 1000).toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }),
        correlation: data.correlation,
      };

      setCorrelationData((prev) => {
        const updated = [...prev, newPoint];
        return updated.slice(-60);
      });
    });

    // Connect to summary WebSocket
    const summaryWs = connectSummary((data: SummaryUpdate) => {
      // Transform backend data to match SummaryStats component expectations
      const transformed = {
        latestPrices: data.symbols?.map((sym) => ({
          symbol: sym.symbol,
          price: sym.price,
          changePercent: sym.change_pct_1m,
        })) || [],
        spread: data.spread?.current || 0,
        zScore: data.spread ? (data.spread.current - data.spread.mean) / (data.spread.std || 1) : 0,
        correlation: data.correlation || 0,
        volatility: data.spread?.std || 0,
        rollingMean: data.spread?.mean || 0,
        rollingVolatility: data.spread?.std || 0,
      };
      console.log('📊 Summary stats updated:', transformed);
      setSummaryStats(transformed);
    });

    // Connect to unified analytics WebSocket for real-time summary updates
    const analyticsWs = connectAnalytics((data: AnalyticsUpdate) => {
      console.log('📈 Analytics update received:', data);
      
      // Update summary stats with latest analytics
      setSummaryStats((prev) => ({
        ...prev,
        latestPrices: Object.entries(data.prices).map(([symbol, price]) => ({
          symbol,
          price,
          changePercent: prev.latestPrices.find(p => p.symbol === symbol)?.changePercent || 0,
        })),
        spread: data.spread,
        zScore: data.z_score,
        correlation: data.correlation,
      }));
      
      // Update spread chart data from analytics stream
      if (typeof data.spread === 'number' && typeof data.z_score === 'number') {
        const newPoint: SpreadDataPoint = {
          timestamp: new Date(data.timestamp).getTime() / 1000,
          time: new Date(data.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          }),
          spread: data.spread,
          zScore: data.z_score,
          upperThreshold: zScoreThreshold,
          lowerThreshold: -zScoreThreshold,
        };
        
        setSpreadData((prev) => {
          const updated = [...prev, newPoint];
          return updated.slice(-60); // Keep last 60 points
        });
      }
    });

    // Connect to alerts WebSocket
    const alertsWs = connectAlerts((data: AlertUpdate) => {
      setAlerts((prev) => [data, ...prev].slice(0, 10)); // Keep last 10 alerts
      
      toast({
        title: `🚨 ${data.type.toUpperCase()} Alert`,
        description: data.message,
        variant: data.severity === 'danger' ? 'destructive' : 'default',
      });
    });

    // Cleanup on unmount
    return () => {
      console.log('🔌 Cleaning up WebSocket connections...');
      pricesWs.close();
      spreadWs.close();
      correlationWs.close();
      summaryWs.close();
      alertsWs.close();
      analyticsWs.close();
    };
  }, [isBackendConnected]);

  // Handle settings changes from ControlPanel
  const handleSettingsChange = async (settings: ControlSettings) => {
    try {
      // Always send all display symbols for price streaming
      await updateSettings({
        selectedSymbols: displaySymbols, // Stream all 3 symbols
        timeframe: settings.timeframe,
        windowSize: settings.windowSize,
        regressionType: settings.regressionType,
        zScoreThreshold: settings.zScoreThreshold,
        correlationThreshold: settings.correlationThreshold,
        volatilityThreshold: settings.volatilityThreshold,
      });
      
      setSelectedSymbols(settings.selectedSymbols); // Store user's pair selection
      setZScoreThreshold(settings.zScoreThreshold);
      setCorrelationThreshold(settings.correlationThreshold);
      setVolatilityThreshold(settings.volatilityThreshold);
      
      toast({
        title: '✅ Settings Updated',
        description: 'Backend configuration updated successfully',
      });
    } catch (error) {
      console.error('Failed to update settings:', error);
      toast({
        title: '❌ Update Failed',
        description: 'Could not update backend settings',
        variant: 'destructive',
      });
    }
  };

  const latestZScore = useMemo(() => {
    return spreadData[spreadData.length - 1]?.zScore || 0;
  }, [spreadData]);

  return (
    <div className="min-h-screen bg-gradient-terminal">
      <DashboardHeader />
      
      <div className="flex">
        <ControlPanel onSettingsChange={handleSettingsChange} />
        
        <main className="flex-1 p-6 overflow-y-auto">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="space-y-6 max-w-[1600px] mx-auto"
          >
            {/* Connection Status */}
            {!isBackendConnected && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4"
              >
                <p className="text-sm text-yellow-500">
                  ⚠️ Backend not connected. Start backend: <code className="bg-black/30 px-2 py-1 rounded">cd BackEnd && python run.py</code>
                </p>
              </motion.div>
            )}

            {/* Summary Stats */}
            <SummaryStats stats={summaryStats} />

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Price Chart - Full Width on Mobile */}
              <div className="lg:col-span-2">
                <PriceChart data={priceData} selectedSymbols={displaySymbols} />
              </div>

              {/* Spread & Z-Score */}
              <SpreadZScoreChart data={spreadData} threshold={zScoreThreshold} />

              {/* Right Column */}
              <div className="space-y-6">
                {/* Correlation */}
                <CorrelationChart data={correlationData} />

                {/* Alerts */}
                <AlertsPanel alerts={alerts} onRemove={removeAlert} />

                {/* Export */}
                <ExportPanel />
              </div>
            </div>

            {/* Footer */}
            <motion.footer 
              className="text-center py-6 border-t border-border"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
            >
              <p className="text-xs text-muted-foreground">
                <span className={`px-2 py-1 rounded mr-2 ${isBackendConnected ? 'bg-green-500/20 text-green-500' : 'bg-secondary'}`}>
                  {isBackendConnected ? '🟢 LIVE' : 'OFFLINE'}
                </span>
                Real-Time Quantitative Market Analytics Dashboard • GEMSCAP 9-Step Implementation
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Python FastAPI Backend + React Frontend • WebSocket Streaming • Binance Live Data
              </p>
            </motion.footer>
          </motion.div>
        </main>
      </div>
    </div>
  );
};

export default Index;
