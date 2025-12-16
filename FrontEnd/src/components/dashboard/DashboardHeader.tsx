import { motion } from 'framer-motion';
import { Activity, Wifi, Clock } from 'lucide-react';
import { useEffect, useState } from 'react';

export const DashboardHeader = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <motion.header 
      className="bg-gradient-hero border-b border-border px-6 py-8"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
    >
      <div className="max-w-full">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Title Section */}
          <div className="space-y-2">
            <motion.div 
              className="flex items-center gap-3"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              <div className="p-2 bg-primary/10 rounded-lg">
                <Activity className="w-6 h-6 text-primary" />
              </div>
              <h1 className="text-2xl lg:text-3xl font-bold tracking-tight">
                <span className="text-gradient-primary">Real-Time Quantitative</span>
                <span className="text-foreground"> Market Analytics</span>
              </h1>
            </motion.div>
            
            <motion.p 
              className="text-muted-foreground text-sm lg:text-base max-w-2xl"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4, duration: 0.5 }}
            >
              Live monitoring and quantitative analysis of cryptocurrency market behavior
            </motion.p>
          </div>

          {/* Status Indicators */}
          <motion.div 
            className="flex items-center gap-6"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            {/* Connection Status */}
            <div className="flex items-center gap-2 px-3 py-2 bg-secondary/50 rounded-lg border border-border">
              <div className="relative">
                <Wifi className="w-4 h-4 text-chart-green" />
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-chart-green rounded-full animate-pulse" />
              </div>
              <span className="text-xs font-medium text-chart-green">
                LIVE
              </span>
            </div>

            {/* Time Display */}
            <div className="flex items-center gap-2 px-3 py-2 bg-secondary/50 rounded-lg border border-border">
              <Clock className="w-4 h-4 text-muted-foreground" />
              <span className="text-xs font-mono text-foreground">
                {currentTime.toLocaleTimeString('en-US', { 
                  hour: '2-digit', 
                  minute: '2-digit', 
                  second: '2-digit',
                  hour12: false 
                })}
              </span>
              <span className="text-xs text-muted-foreground">UTC</span>
            </div>
          </motion.div>
        </div>

        {/* Subtitle Banner */}
        <motion.div 
          className="mt-6 flex items-center gap-2 text-xs text-muted-foreground"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.5 }}
        >
          <span className="px-2 py-1 bg-chart-green/10 text-chart-green rounded font-medium">
            LIVE
          </span>
          <span>•</span>
          <span>Real-Time Quantitative Market Analytics Dashboard • GEMSCAP 9-Step Implementation</span>
          <span>•</span>
          <span>Python FastAPI Backend + React Frontend • WebSocket Streaming • Binance Live Data</span>
        </motion.div>
      </div>
    </motion.header>
  );
};
