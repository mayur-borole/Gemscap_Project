import { motion } from 'framer-motion';
import { TrendingUp, Maximize2 } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Brush,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export interface PriceDataPoint {
  timestamp: number;
  time: string;
  [key: string]: number | string;
}

interface PriceChartProps {
  data: PriceDataPoint[];
  selectedSymbols?: string[];
}

const CHART_COLORS: Record<string, string> = {
  BTCUSDT: '#00d4aa',
  ETHUSDT: '#a855f7',
  SOLUSDT: '#f97316',
  BNBUSDT: '#f59e0b',
  XRPUSDT: '#3b82f6',
  ADAUSDT: '#06b6d4',
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-popover/95 backdrop-blur-sm border border-border rounded-lg p-3 shadow-xl">
        <p className="text-xs text-muted-foreground mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div 
              className="w-2 h-2 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-muted-foreground">{entry.name}:</span>
            <span className="font-mono font-medium text-foreground">
              ${entry.value?.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export const PriceChart = ({ data, selectedSymbols = ['BTCUSDT', 'ETHUSDT'] }: PriceChartProps) => {
  console.log('📈 PriceChart rendering with', data.length, 'data points');
  
  // Extract available symbols dynamically from data
  const availableSymbols = data.length > 0 
    ? Object.keys(data[0]).filter(key => key !== 'timestamp' && key !== 'time')
    : selectedSymbols;
  
  // Use selected symbols or fall back to available symbols
  const symbolsToDisplay = selectedSymbols.length > 0 
    ? selectedSymbols.filter(sym => availableSymbols.includes(sym))
    : availableSymbols;
  
  if (!data || data.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <Card className="card-glow bg-card/80 backdrop-blur-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-primary/10 rounded">
                <TrendingUp className="w-4 h-4 text-primary" />
              </div>
              <CardTitle className="text-base font-medium">Price Charts</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <div className="animate-pulse mb-2">📊</div>
                <p className="text-sm">Waiting for price data...</p>
                <p className="text-xs mt-1">WebSocket is connecting...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      <Card className="card-glow bg-card/80 backdrop-blur-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-primary/10 rounded">
              <TrendingUp className="w-4 h-4 text-primary" />
            </div>
            <CardTitle className="text-base font-medium">Price Charts</CardTitle>
            <span className="text-xs text-muted-foreground">({data.length} points)</span>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Maximize2 className="w-4 h-4 text-muted-foreground" />
          </Button>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  {Object.entries(CHART_COLORS).map(([key, color]) => (
                    <linearGradient key={key} id={`gradient-${key}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={color} stopOpacity={0} />
                    </linearGradient>
                  ))}
                </defs>
                <CartesianGrid 
                  strokeDasharray="3 3" 
                  stroke="hsl(var(--border))" 
                  opacity={0.3}
                  vertical={false}
                />
                <XAxis 
                  dataKey="time" 
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  tickLine={{ stroke: 'hsl(var(--border))' }}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                />
                <YAxis 
                  yAxisId="left"
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  tickLine={{ stroke: 'hsl(var(--border))' }}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
                  domain={[(dataMin: number) => dataMin * 0.9995, (dataMax: number) => dataMax * 1.0005]}
                />
                <YAxis 
                  yAxisId="right"
                  orientation="right"
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  tickLine={{ stroke: 'hsl(var(--border))' }}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                  domain={[(dataMin: number) => dataMin * 0.998, (dataMax: number) => dataMax * 1.002]}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  wrapperStyle={{ paddingTop: '20px' }}
                  formatter={(value) => <span className="text-foreground text-sm">{value}</span>}
                />
                {/* Dynamically render lines for each symbol */}
                {symbolsToDisplay.map((symbol, index) => {
                  // Determine which Y-axis to use based on price magnitude
                  // BTC uses left axis (>$50k), ETH/SOL use right axis for better visibility
                  const latestPrice = data.length > 0 ? data[data.length - 1][symbol] : 0;
                  const useRightAxis = typeof latestPrice === 'number' && latestPrice < 50000;
                  
                  return (
                    <Line
                      key={symbol}
                      yAxisId={useRightAxis ? 'right' : 'left'}
                      type="monotone"
                      dataKey={symbol}
                      name={symbol.replace('USDT', '/USDT')}
                      stroke={CHART_COLORS[symbol] || `hsl(${(index * 137.5) % 360}, 70%, 50%)`}
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4, strokeWidth: 2 }}
                    />
                  );
                })}
                <Brush 
                  dataKey="time" 
                  height={25} 
                  stroke="hsl(var(--primary))"
                  fill="hsl(var(--secondary))"
                  tickFormatter={() => ''}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
