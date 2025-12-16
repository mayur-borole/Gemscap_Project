import { motion } from 'framer-motion';
import { Download, FileSpreadsheet, FileText, Database } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { toast } from '@/hooks/use-toast';
import { exportData, downloadExportedData } from '@/services/api';
import { useState } from 'react';

export const ExportPanel = () => {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: 'csv' | 'json' | 'parquet') => {
    setIsExporting(true);
    
    try {
      toast({
        title: "🔄 Exporting Data...",
        description: `Fetching ${format.toUpperCase()} data from backend...`,
      });

      const data = await exportData(format, '1m', 1000);
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const filename = `gemscap_export_${timestamp}.${format}`;
      
      downloadExportedData(data, filename);
      
      toast({
        title: "✅ Export Complete",
        description: `Successfully exported data as ${filename}`,
      });
    } catch (error) {
      console.error('Export failed:', error);
      toast({
        title: "❌ Export Failed",
        description: "Make sure backend is running and has data available.",
        variant: 'destructive',
      });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.6 }}
    >
      <Card className="card-glow bg-card/80 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-primary/10 rounded">
              <Download className="w-4 h-4 text-primary" />
            </div>
            <CardTitle className="text-base font-medium">Data Export</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-3">
            <Button 
              variant="secondary" 
              className="flex flex-col h-auto py-4 gap-2"
              onClick={() => handleExport('csv')}
              disabled={isExporting}
            >
              <FileSpreadsheet className="w-5 h-5 text-chart-green" />
              <span className="text-xs">CSV</span>
            </Button>
            <Button 
              variant="secondary" 
              className="flex flex-col h-auto py-4 gap-2"
              onClick={() => handleExport('json')}
              disabled={isExporting}
            >
              <FileText className="w-5 h-5 text-chart-orange" />
              <span className="text-xs">JSON</span>
            </Button>
            <Button 
              variant="secondary" 
              className="flex flex-col h-auto py-4 gap-2"
              onClick={() => handleExport('parquet')}
              disabled={isExporting}
            >
              <Database className="w-5 h-5 text-chart-purple" />
              <span className="text-xs">Parquet</span>
            </Button>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-3">
            {isExporting ? '⏳ Exporting...' : '📦 Click to export data from Python backend'}
          </p>
        </CardContent>
      </Card>
    </motion.div>
  );
};
