import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Terminal, 
  Download, 
  Search, 
  X, 
  ChevronDown, 
  Filter,
  Clock,
  Copy,
  Check
} from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  source?: string;
}

interface LogViewerProps {
  logs?: string[] | LogEntry[];
  isLive?: boolean;
  className?: string;
  title?: string;
  onDownload?: () => void;
}

const LogViewer: React.FC<LogViewerProps> = ({ 
  logs = [], 
  isLive = false, 
  className = '', 
  title = 'Logs',
  onDownload
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // Convert string logs to LogEntry format
  const processedLogs: LogEntry[] = logs.map((log, index) => {
    if (typeof log === 'string') {
      const level = log.includes('❌') || log.includes('ERROR') ? 'error' :
                   log.includes('⚠️') || log.includes('WARN') ? 'warning' :
                   log.includes('✅') || log.includes('SUCCESS') ? 'success' : 'info';
      
      return {
        id: `log-${index}`,
        timestamp: new Date().toISOString(),
        level,
        message: log,
        source: 'deployment'
      };
    }
    return log;
  });

  // Filter logs based on search and level
  const filteredLogs = processedLogs.filter(log => {
    const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLevel = levelFilter === 'all' || log.level === levelFilter;
    return matchesSearch && matchesLevel;
  });

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && endRef.current) {
      endRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const getLevelColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return 'text-red-400';
      case 'warning':
        return 'text-yellow-400';
      case 'success':
        return 'text-green-400';
      default:
        return 'text-gray-300';
    }
  };

  const getLevelIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'success':
        return '✅';
      default:
        return '📝';
    }
  };

  const copyLogs = async () => {
    const logText = filteredLogs.map(log => 
      `[${new Date(log.timestamp).toLocaleTimeString()}] ${log.message}`
    ).join('\n');
    
    try {
      await navigator.clipboard.writeText(logText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy logs:', err);
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
            <Terminal className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 dark:text-white">{title}</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {filteredLogs.length} entries
              {isLive && <span className="ml-2 text-green-500">● Live</span>}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-3 h-3 text-gray-400" />
            <input
              type="text"
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-7 pr-3 py-1 text-xs bg-gray-100 dark:bg-gray-800 border-0 rounded focus:outline-none focus:ring-1 focus:ring-primary-500 w-32"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-2 top-1/2 transform -translate-y-1/2"
              >
                <X className="w-3 h-3 text-gray-400 hover:text-gray-600" />
              </button>
            )}
          </div>

          {/* Level Filter */}
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="text-xs bg-gray-100 dark:bg-gray-800 border-0 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            <option value="all">All</option>
            <option value="info">Info</option>
            <option value="success">Success</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>

          {/* Auto-scroll toggle */}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-1 rounded text-xs ${
              autoScroll 
                ? 'bg-primary-100 text-primary-600 dark:bg-primary-900 dark:text-primary-400' 
                : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
            }`}
            title="Auto-scroll"
          >
            <ChevronDown className="w-3 h-3" />
          </button>

          {/* Copy */}
          <button
            onClick={copyLogs}
            className="p-1 rounded text-xs bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
            title="Copy logs"
          >
            {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
          </button>

          {/* Download */}
          {onDownload && (
            <button
              onClick={onDownload}
              className="p-1 rounded text-xs bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
              title="Download logs"
            >
              <Download className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Log Content */}
      <div 
        ref={logContainerRef}
        className="h-64 overflow-y-auto bg-gray-900 text-gray-100 font-mono text-xs"
        style={{ height: className.includes('h-') ? undefined : '16rem' }}
      >
        <div className="p-4 space-y-1">
          <AnimatePresence initial={false}>
            {filteredLogs.map((log, index) => (
              <motion.div
                key={log.id}
                initial={isLive ? { opacity: 0, x: -20 } : false}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
                className="flex items-start gap-3 py-1 hover:bg-gray-800 rounded px-2 -mx-2 transition-colors"
              >
                <span className="text-gray-500 text-xs mt-0.5 flex-shrink-0">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="flex-shrink-0 mt-0.5">
                  {getLevelIcon(log.level)}
                </span>
                <span className={`flex-1 ${getLevelColor(log.level)}`}>
                  {log.message}
                </span>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {filteredLogs.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              {searchTerm || levelFilter !== 'all' ? 'No logs match your filters' : 'No logs available'}
            </div>
          )}
          
          <div ref={endRef} />
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <div className="flex items-center gap-2">
            <Clock className="w-3 h-3" />
            <span>Last updated: {new Date().toLocaleTimeString()}</span>
          </div>
          {filteredLogs.length !== processedLogs.length && (
            <span>{filteredLogs.length} of {processedLogs.length} entries shown</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default LogViewer;