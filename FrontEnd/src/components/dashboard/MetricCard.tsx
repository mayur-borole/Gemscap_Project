import { motion } from 'framer-motion';
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: number;
  changeLabel?: string;
  icon: LucideIcon;
  iconColor?: string;
  delay?: number;
  highlight?: boolean;
  format?: 'currency' | 'percentage' | 'number' | 'sigma';
}

export const MetricCard = ({
  title,
  value,
  subtitle,
  change,
  changeLabel,
  icon: Icon,
  iconColor = 'text-primary',
  delay = 0,
  highlight = false,
  format = 'number',
}: MetricCardProps) => {
  const formatValue = (val: string | number) => {
    if (typeof val === 'string') return val;
    switch (format) {
      case 'currency':
        return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      case 'percentage':
        return `${val.toFixed(2)}%`;
      case 'sigma':
        return `${val.toFixed(2)}σ`;
      default:
        return val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 });
    }
  };

  const getChangeIcon = () => {
    if (!change) return <Minus className="w-3 h-3" />;
    return change > 0 
      ? <TrendingUp className="w-3 h-3" /> 
      : <TrendingDown className="w-3 h-3" />;
  };

  const getChangeColor = () => {
    if (!change) return 'text-muted-foreground';
    return change > 0 ? 'text-chart-green' : 'text-chart-red';
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, delay: delay * 0.1 }}
      className="h-full"
    >
      <Card className={cn(
        "card-glow bg-card/80 backdrop-blur-sm transition-all duration-300 h-full",
        highlight && "metric-pulse border-primary/50"
      )}>
        <CardContent className="p-4 h-full">
          <div className="flex items-center justify-between gap-3 h-full">
            {/* Left: Text Content */}
            <div className="flex flex-col justify-center min-w-0 flex-1">
              <p className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium truncate">
                {title}
              </p>
              <motion.p 
                className="text-xl font-bold font-mono text-foreground mt-1 truncate"
                key={String(value)}
                initial={{ opacity: 0.5 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.2 }}
              >
                {formatValue(value)}
              </motion.p>
              {subtitle && (
                <p className="text-[10px] text-muted-foreground mt-0.5 truncate">{subtitle}</p>
              )}
              {change !== undefined && (
                <div className={cn("flex items-center gap-1 text-[11px] mt-1", getChangeColor())}>
                  {getChangeIcon()}
                  <span className="font-mono font-medium">
                    {change > 0 ? '+' : ''}{change.toFixed(2)}%
                  </span>
                </div>
              )}
            </div>
            
            {/* Right: Icon */}
            <div className={cn(
              "flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center",
              "bg-primary/10"
            )}>
              <Icon className={cn("w-5 h-5", iconColor)} />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};
