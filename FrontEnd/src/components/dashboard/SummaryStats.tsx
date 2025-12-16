import { motion } from 'framer-motion';
import { 
  DollarSign, 
  Activity, 
  Gauge, 
  BarChart3, 
  TrendingUp,
  GitBranch 
} from 'lucide-react';
import { MetricCard } from './MetricCard';

interface SummaryStatsType {
  latestPrices: Array<{
    symbol: string;
    price: number;
    changePercent: number;
  }>;
  spread: number;
  zScore: number;
  correlation: number;
  volatility?: number;
  rollingMean?: number;
  rollingVolatility?: number;
}

interface SummaryStatsProps {
  stats: SummaryStatsType;
}

export const SummaryStats = ({ stats }: SummaryStatsProps) => {
  // Safety check: return placeholder if stats not yet loaded
  if (!stats || !stats.latestPrices || stats.latestPrices.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="space-y-4"
      >
        <h3 className="text-sm uppercase tracking-wider text-muted-foreground font-medium">
          Summary Statistics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="col-span-full text-center text-muted-foreground py-8">
            Loading data from backend...
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.4 }}
      className="space-y-4"
    >
      <h3 className="text-sm uppercase tracking-wider text-muted-foreground font-medium">
        Summary Statistics
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Latest Prices */}
        {stats.latestPrices.map((price, index) => (
          <MetricCard
            key={price.symbol}
            title={price.symbol}
            value={price.price}
            format="currency"
            change={price.changePercent}
            icon={DollarSign}
            iconColor={price.changePercent >= 0 ? 'text-chart-green' : 'text-chart-red'}
            delay={index}
          />
        ))}

        {/* Spread */}
        <MetricCard
          title="Spread"
          value={stats.spread}
          format="number"
          icon={Activity}
          iconColor="text-chart-purple"
          delay={3}
        />

        {/* Z-Score */}
        <MetricCard
          title="Z-Score"
          value={stats.zScore}
          format="sigma"
          icon={Gauge}
          iconColor={Math.abs(stats.zScore) > 2 ? 'text-alert-danger' : 'text-chart-orange'}
          delay={4}
          highlight={Math.abs(stats.zScore) > 2}
        />

        {/* Correlation */}
        <MetricCard
          title="Correlation"
          value={stats.correlation}
          format="number"
          icon={GitBranch}
          iconColor="text-chart-cyan"
          delay={5}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Rolling Mean */}
        <MetricCard
          title="Rolling Mean"
          value={stats.rollingMean}
          format="currency"
          subtitle="20-period SMA"
          icon={BarChart3}
          iconColor="text-primary"
          delay={6}
        />

        {/* Rolling Volatility */}
        <MetricCard
          title="Rolling Volatility"
          value={stats.rollingVolatility}
          format="currency"
          subtitle="20-period StdDev"
          icon={TrendingUp}
          iconColor="text-chart-yellow"
          delay={7}
        />
      </div>
    </motion.div>
  );
};
