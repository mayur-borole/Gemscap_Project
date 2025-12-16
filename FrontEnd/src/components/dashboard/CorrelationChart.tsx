import { motion } from 'framer-motion';
import { GitBranch } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface CorrelationDataPoint {
  timestamp: number;
  time: string;
  correlation: number;
}

interface CorrelationChartProps {
  data: CorrelationDataPoint[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const correlation = payload[0]?.value;
    const strength = Math.abs(correlation) > 0.8 
      ? 'Strong' 
      : Math.abs(correlation) > 0.5 
        ? 'Moderate' 
        : 'Weak';
    const direction = correlation >= 0 ? 'Positive' : 'Negative';
    
    return (
      <div className="bg-popover/95 backdrop-blur-sm border border-border rounded-lg p-3 shadow-xl">
        <p className="text-xs text-muted-foreground mb-2">{label}</p>
        <div className="flex items-center gap-2 text-sm">
          <div className="w-2 h-2 rounded-full bg-chart-cyan" />
          <span className="text-muted-foreground">Correlation:</span>
          <span className="font-mono font-medium text-foreground">
            {correlation?.toFixed(4)}
          </span>
        </div>
        <div className="mt-2 text-xs text-muted-foreground">
          {strength} {direction} Correlation
        </div>
      </div>
    );
  }
  return null;
};

const CorrelationScale = ({ value }: { value: number }) => {
  const position = ((value + 1) / 2) * 100;
  
  return (
    <div className="mt-4 px-2">
      <div className="relative h-3 rounded-full overflow-hidden bg-gradient-to-r from-chart-red via-muted to-chart-green">
        <motion.div 
          className="absolute top-0 w-1 h-full bg-foreground shadow-lg"
          initial={{ left: '50%' }}
          animate={{ left: `${position}%` }}
          transition={{ type: 'spring', stiffness: 100, damping: 15 }}
          style={{ transform: 'translateX(-50%)' }}
        />
      </div>
      <div className="flex justify-between mt-1 text-xs text-muted-foreground">
        <span>-1.0</span>
        <span>0</span>
        <span>+1.0</span>
      </div>
    </div>
  );
};

export const CorrelationChart = ({ data }: CorrelationChartProps) => {
  const latestCorrelation = data[data.length - 1]?.correlation || 0;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
    >
      <Card className="card-glow bg-card/80 backdrop-blur-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-chart-cyan/20 rounded">
              <GitBranch className="w-4 h-4 text-chart-cyan" />
            </div>
            <CardTitle className="text-base font-medium">Rolling Correlation</CardTitle>
          </div>
          <div className="text-right">
            <div className={`text-lg font-mono font-bold ${
              latestCorrelation >= 0 ? 'text-chart-green' : 'text-chart-red'
            }`}>
              {latestCorrelation.toFixed(4)}
            </div>
            <div className="text-xs text-muted-foreground">
              BTC ↔ ETH
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="correlationGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00d4aa" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#00d4aa" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} vertical={false} />
                <XAxis 
                  dataKey="time" 
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                />
                <YAxis 
                  domain={[-1, 1]}
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }}
                  axisLine={{ stroke: 'hsl(var(--border))' }}
                  ticks={[-1, -0.5, 0, 0.5, 1]}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="5 5" />
                <ReferenceLine y={0.8} stroke="hsl(var(--chart-green))" strokeDasharray="3 3" opacity={0.5} />
                <ReferenceLine y={-0.8} stroke="hsl(var(--chart-red))" strokeDasharray="3 3" opacity={0.5} />
                <Line
                  type="monotone"
                  dataKey="correlation"
                  name="Correlation"
                  stroke="#00d4aa"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <CorrelationScale value={latestCorrelation} />
        </CardContent>
      </Card>
    </motion.div>
  );
};
