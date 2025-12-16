import { motion } from 'framer-motion';
import { 
  Settings, 
  RefreshCw, 
  Play, 
  Pause,
  ChevronDown,
  TestTube,
  Download
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { AVAILABLE_SYMBOLS, TIMEFRAMES, REGRESSION_TYPES } from '@/lib/mockData';
import { Badge } from '@/components/ui/badge';

interface ControlPanelProps {
  onSettingsChange?: (settings: ControlSettings) => void;
}

export interface ControlSettings {
  selectedSymbols: string[];
  timeframe: string;
  windowSize: number;
  regressionType: string;
  zScoreThreshold: number;
  correlationThreshold: number;
  volatilityThreshold: number;
  isLive: boolean;
}

export const ControlPanel = ({ onSettingsChange }: ControlPanelProps) => {
  const [isOpen, setIsOpen] = useState(true);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['BTCUSDT', 'ETHUSDT']);
  const [timeframe, setTimeframe] = useState('1m');
  const [windowSize, setWindowSize] = useState([20]);
  const [regressionType, setRegressionType] = useState('ols');
  const [zScoreThreshold, setZScoreThreshold] = useState([2]);
  const [correlationThreshold, setCorrelationThreshold] = useState([0.5]);
  const [volatilityThreshold, setVolatilityThreshold] = useState([1000]);
  const [isLive, setIsLive] = useState(true);

  const toggleSymbol = (symbol: string) => {
    setSelectedSymbols(prev => {
      if (prev.includes(symbol)) {
        // Don't allow deselecting if only 2 remaining
        if (prev.length <= 2) return prev;
        return prev.filter(s => s !== symbol);
      } else {
        // Only allow selecting if less than 2
        if (prev.length >= 2) {
          // Replace the second symbol
          return [prev[0], symbol];
        }
        return [...prev, symbol];
      }
    });
  };

  // Send settings to backend when they change
  const applySettings = () => {
    if (onSettingsChange) {
      onSettingsChange({
        selectedSymbols,
        timeframe,
        windowSize: windowSize[0],
        regressionType,
        zScoreThreshold: zScoreThreshold[0],
        correlationThreshold: correlationThreshold[0],
        volatilityThreshold: volatilityThreshold[0],
        isLive,
      });
    }
  };

  // Apply settings when user changes them (with debounce)
  useEffect(() => {
    const timer = setTimeout(() => {
      applySettings();
    }, 1000); // Wait 1 second after user stops changing values

    return () => clearTimeout(timer);
  }, [selectedSymbols, timeframe, windowSize, regressionType, zScoreThreshold, correlationThreshold, volatilityThreshold, isLive]);

  const containerVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        duration: 0.4,
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <motion.aside 
      className="w-80 bg-sidebar border-r border-sidebar-border p-4 overflow-y-auto"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Panel Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-primary" />
          <h2 className="font-semibold text-foreground">Control Panel</h2>
        </div>
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-8 w-8"
          onClick={() => setIsLive(!isLive)}
        >
          {isLive ? (
            <Pause className="w-4 h-4 text-chart-green" />
          ) : (
            <Play className="w-4 h-4 text-muted-foreground" />
          )}
        </Button>
      </div>

      <div className="space-y-6">
        {/* Symbol Selection */}
        <motion.div variants={itemVariants} className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">
              Comparison Pair
            </Label>
            <span className="text-xs text-primary font-mono">{selectedSymbols.length}/2</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {AVAILABLE_SYMBOLS.map((symbol) => (
              <Badge
                key={symbol.value}
                variant={selectedSymbols.includes(symbol.value) ? "default" : "secondary"}
                className={`cursor-pointer transition-all duration-200 ${
                  selectedSymbols.includes(symbol.value) 
                    ? 'bg-primary text-primary-foreground hover:bg-primary/90' 
                    : 'bg-secondary hover:bg-secondary/80'
                }`}
                onClick={() => toggleSymbol(symbol.value)}
              >
                {symbol.label}
              </Badge>
            ))}
          </div>
        </motion.div>

        {/* Timeframe Selection */}
        <motion.div variants={itemVariants} className="space-y-3">
          <Label className="text-xs uppercase tracking-wider text-muted-foreground">
            Timeframe
          </Label>
          <Select value={timeframe} onValueChange={setTimeframe}>
            <SelectTrigger className="bg-secondary border-border">
              <SelectValue placeholder="Select timeframe" />
            </SelectTrigger>
            <SelectContent className="bg-popover border-border">
              {TIMEFRAMES.map((tf) => (
                <SelectItem key={tf.value} value={tf.value}>
                  {tf.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </motion.div>

        {/* Rolling Window Size */}
        <motion.div variants={itemVariants} className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">
              Rolling Window
            </Label>
            <span className="font-mono text-sm text-primary">{windowSize[0]}</span>
          </div>
          <Slider
            value={windowSize}
            onValueChange={setWindowSize}
            min={5}
            max={100}
            step={5}
            className="py-2"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>5</span>
            <span>100 periods</span>
          </div>
        </motion.div>

        {/* Regression Type */}
        <motion.div variants={itemVariants} className="space-y-3">
          <Label className="text-xs uppercase tracking-wider text-muted-foreground">
            Regression Type
          </Label>
          <Select value={regressionType} onValueChange={setRegressionType}>
            <SelectTrigger className="bg-secondary border-border">
              <SelectValue placeholder="Select regression" />
            </SelectTrigger>
            <SelectContent className="bg-popover border-border">
              {REGRESSION_TYPES.map((rt) => (
                <SelectItem key={rt.value} value={rt.value}>
                  {rt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </motion.div>

        {/* ADF Test Button */}
        <motion.div variants={itemVariants}>
          <Button 
            variant="outline" 
            className="w-full justify-start gap-2 border-border hover:bg-secondary"
          >
            <TestTube className="w-4 h-4" />
            Run ADF Test
            <span className="ml-auto text-xs text-muted-foreground">(UI Only)</span>
          </Button>
        </motion.div>

        {/* Z-Score Threshold */}
        <motion.div variants={itemVariants} className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">
              Z-Score Threshold
            </Label>
            <span className="font-mono text-sm text-chart-orange">±{zScoreThreshold[0]}</span>
          </div>
          <Slider
            value={zScoreThreshold}
            onValueChange={setZScoreThreshold}
            min={1}
            max={4}
            step={0.1}
            className="py-2"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>±1.0</span>
            <span>±4.0 σ</span>
          </div>
        </motion.div>

        {/* Correlation Threshold */}
        <motion.div variants={itemVariants} className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">
              Correlation Threshold
            </Label>
            <span className="font-mono text-sm text-chart-purple">{correlationThreshold[0].toFixed(2)}</span>
          </div>
          <Slider
            value={correlationThreshold}
            onValueChange={setCorrelationThreshold}
            min={0.1}
            max={1}
            step={0.05}
            className="py-2"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>0.1</span>
            <span>1.0</span>
          </div>
        </motion.div>

        {/* Volatility Threshold */}
        <motion.div variants={itemVariants} className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-xs uppercase tracking-wider text-muted-foreground">
              Volatility Threshold
            </Label>
            <span className="font-mono text-sm text-chart-red">{volatilityThreshold[0]}</span>
          </div>
          <Slider
            value={volatilityThreshold}
            onValueChange={setVolatilityThreshold}
            min={100}
            max={5000}
            step={100}
            className="py-2"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>100</span>
            <span>5000</span>
          </div>
        </motion.div>

        {/* Live Toggle */}
        <motion.div variants={itemVariants} className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg border border-border">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-chart-green animate-pulse' : 'bg-muted-foreground'}`} />
            <Label className="text-sm">Live Updates</Label>
          </div>
          <Switch checked={isLive} onCheckedChange={setIsLive} />
        </motion.div>

        {/* Refresh Button */}
        <motion.div variants={itemVariants}>
          <Button className="w-full btn-glow gap-2" disabled={!isLive}>
            <RefreshCw className={`w-4 h-4 ${isLive ? 'animate-spin' : ''}`} style={{ animationDuration: '3s' }} />
            {isLive ? 'Auto-Refreshing' : 'Paused'}
          </Button>
        </motion.div>

        {/* Advanced Settings Collapsible */}
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between">
              <span className="text-xs uppercase tracking-wider text-muted-foreground">
                Advanced Settings
              </span>
              <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-4 pt-4">
            <motion.div variants={itemVariants} className="space-y-3">
              <Label className="text-xs uppercase tracking-wider text-muted-foreground">
                Data Source
              </Label>
              <div className="p-3 bg-secondary/30 rounded-lg border border-dashed border-border">
                <p className="text-xs text-muted-foreground">
                  Binance WebSocket (Pending Python Backend)
                </p>
              </div>
            </motion.div>

            <Button 
              variant="secondary" 
              className="w-full justify-start gap-2"
            >
              <Download className="w-4 h-4" />
              Download Analytics (CSV)
              <span className="ml-auto text-xs text-muted-foreground">(UI)</span>
            </Button>
          </CollapsibleContent>
        </Collapsible>
      </div>
    </motion.aside>
  );
};
