import { motion } from 'framer-motion';
import { Activity, AlertTriangle } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface SpreadDataPoint {
  timestamp: number;
  time: string;
  spread: number;
  zScore: number;
  upperThreshold: number;
  lowerThreshold: number;
}

interface SpreadZScoreChartProps {
  data: SpreadDataPoint[];
  threshold?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const zScore = payload.find((p: any) => p.dataKey === 'zScore')?.value;
    const isAlert = Math.abs(zScore) > 2;
    
    return (
      <div className={`bg-popover/95 backdrop-blur-sm border rounded-lg p-3 shadow-xl ${isAlert ? 'border-alert-danger' : 'border-border'}`}>
        <p className="text-xs text-muted-foreground mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div 
              className="w-2 h-2 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-muted-foreground">{entry.name}:</span>
            <span className={`font-mono font-medium ${
              entry.dataKey === 'zScore' 
                ? Math.abs(entry.value) > 2 
                  ? 'text-alert-danger' 
                  : 'text-foreground'
                : 'text-foreground'
            }`}>
              {entry.value?.toFixed(3)}
            </span>
          </div>
        ))}
        {isAlert && (
          <div className="flex items-center gap-1 mt-2 text-xs text-alert-danger">
            <AlertTriangle className="w-3 h-3" />
            <span>Threshold breach detected</span>
          </div>
        )}
      </div>
    );
  }
  return null;
};

export const SpreadZScoreChart = ({ data, threshold = 2 }: SpreadZScoreChartProps) => {
  console.log('📊 SpreadZScoreChart rendering with', data.length, 'data points');
  
  // Check if any current z-score exceeds threshold
  const latestZScore = data[data.length - 1]?.zScore || 0;
  const isInAlert = Math.abs(latestZScore) > threshold;
  
  if (!data || data.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="space-y-4"
      >
        <Card className="card-glow bg-card/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-base font-medium">Spread & Z-Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[180px] flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <div className="animate-pulse mb-2">📊</div>
                <p className="text-sm">Waiting for spread data...</p>
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
      transition={{ duration: 0.5, delay: 0.2 }}
      className="space-y-4"
    >
      {/* Spread Chart */}
      <Card className="card-glow bg-card/80 backdrop-blur-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-chart-purple/20 rounded">
              <Activity className="w-4 h-4 text-chart-purple" />
            </div>
            <CardTitle className="text-base font-medium">Price Spread</CardTitle>
          </div>
          <span className="text-xs font-mono text-muted-foreground">
            BTC - ETH (Normalized)
          </span>
        </CardHeader>
        <CardContent>
          <div className="h-[180px] chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="spreadGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} vertical={false} />
                <XAxis 
                  dataKey="time" 
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                />
                <YAxis 
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="5 5" />
                <Area
                  type="monotone"
                  dataKey="spread"
                  fill="url(#spreadGradient)"
                  stroke="#a855f7"
                  strokeWidth={2}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Z-Score Chart */}
      <Card className={`card-glow bg-card/80 backdrop-blur-sm ${isInAlert ? 'alert-glow-danger' : ''}`}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded ${isInAlert ? 'bg-alert-danger/20' : 'bg-chart-orange/20'}`}>
              <Activity className={`w-4 h-4 ${isInAlert ? 'text-alert-danger' : 'text-chart-orange'}`} />
            </div>
            <CardTitle className="text-base font-medium">Z-Score</CardTitle>
            {isInAlert && (
              <span className="px-2 py-0.5 text-xs font-medium bg-alert-danger/20 text-alert-danger rounded-full animate-pulse">
                ALERT
              </span>
            )}
          </div>
          <span className={`text-lg font-mono font-bold ${
            isInAlert ? 'text-alert-danger' : 'text-foreground'
          }`}>
            {latestZScore.toFixed(2)}σ
          </span>
        </CardHeader>
        <CardContent>
          <div className="h-[180px] chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="zScoreGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} vertical={false} />
                <XAxis 
                  dataKey="time" 
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                />
                <YAxis 
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                  domain={[-4, 4]}
                />
                <Tooltip content={<CustomTooltip />} />
                {/* Threshold Lines */}
                <ReferenceLine 
                  y={threshold} 
                  stroke="hsl(var(--alert-warning))" 
                  strokeDasharray="5 5" 
                  label={{ 
                    value: `+${threshold}σ`, 
                    position: 'right',
                    fill: 'hsl(var(--alert-warning))',
                    fontSize: 10
                  }}
                />
                <ReferenceLine 
                  y={-threshold} 
                  stroke="hsl(var(--alert-warning))" 
                  strokeDasharray="5 5"
                  label={{ 
                    value: `-${threshold}σ`, 
                    position: 'right',
                    fill: 'hsl(var(--alert-warning))',
                    fontSize: 10
                  }}
                />
                <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="3 3" />
                <Line
                  type="monotone"
                  dataKey="zScore"
                  name="Z-Score"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
