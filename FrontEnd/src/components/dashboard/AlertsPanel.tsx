import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, CheckCircle, Bell, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface Alert {
  type: string;
  severity: string;
  message: string;
  timestamp: string;
  symbol?: string;
  value?: number;
}

interface AlertsPanelProps {
  alerts: Alert[];
  onRemove: (index: number) => void;
}

export const AlertsPanel = ({ alerts, onRemove }: AlertsPanelProps) => {

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.5 }}
    >
      <Card className={cn(
        "card-glow bg-card/80 backdrop-blur-sm transition-all duration-300",
        alerts.length > 0 && "border-alert-danger/50 alert-glow-danger"
      )}>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div className="flex items-center gap-2">
            <div className={cn(
              "p-1.5 rounded",
              alerts.length > 0 ? "bg-alert-danger/20" : "bg-chart-green/20"
            )}>
              <Bell className={cn(
                "w-4 h-4",
                alerts.length > 0 ? "text-alert-danger" : "text-chart-green"
              )} />
            </div>
            <CardTitle className="text-base font-medium">Alerts</CardTitle>
            {alerts.length > 0 && (
              <span className="px-2 py-0.5 text-xs font-medium bg-alert-danger/20 text-alert-danger rounded-full animate-pulse">
                {alerts.length} Active
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <AnimatePresence mode="wait">
            {alerts.length === 0 ? (
              <motion.div
                key="no-alerts"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="flex items-center gap-3 p-4 bg-chart-green/10 border border-chart-green/20 rounded-lg"
              >
                <CheckCircle className="w-5 h-5 text-chart-green" />
                <div>
                  <p className="text-sm font-medium text-chart-green">No Active Alerts</p>
                  <p className="text-xs text-muted-foreground">
                    All metrics within normal thresholds
                  </p>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="alerts"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-3"
              >
                {alerts.map((alert, index) => (
                  <motion.div
                    key={`${alert.timestamp}-${index}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={cn(
                      "flex items-start gap-3 p-4 rounded-lg border",
                      alert.severity === 'danger' && "bg-alert-danger/10 border-alert-danger/30",
                      alert.severity === 'warning' && "bg-alert-warning/10 border-alert-warning/30",
                      alert.severity === 'info' && "bg-primary/10 border-primary/30"
                    )}
                  >
                    <AlertTriangle className={cn(
                      "w-5 h-5 mt-0.5 flex-shrink-0",
                      alert.severity === 'danger' && "text-alert-danger",
                      alert.severity === 'warning' && "text-alert-warning",
                      alert.severity === 'info' && "text-primary"
                    )} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className={cn(
                          "text-sm font-medium",
                          alert.severity === 'danger' && "text-alert-danger",
                          alert.severity === 'warning' && "text-alert-warning",
                          alert.severity === 'info' && "text-primary"
                        )}>
                          {alert.type}
                        </p>
                        <span className="text-xs text-muted-foreground flex-shrink-0">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {alert.message}
                      </p>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-6 w-6 flex-shrink-0"
                      onClick={() => onRemove(index)}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>
  );
};
