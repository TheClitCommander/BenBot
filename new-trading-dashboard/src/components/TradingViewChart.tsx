import { useEffect, useRef } from 'react';

interface TradingViewChartProps {
  symbol?: string;
  interval?: string;
  theme?: 'light' | 'dark';
  autosize?: boolean;
  height?: number;
  width?: number;
}

const TradingViewChart = ({
  symbol = 'BTCUSDT',
  interval = '60', // Default to 1 hour chart
  theme = 'light',
  autosize = true,
  height = 500,
  width = 800,
}: TradingViewChartProps) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Create a script element for the TradingView Widget
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (typeof window.TradingView !== 'undefined' && containerRef.current) {
        new window.TradingView.widget({
          autosize,
          symbol,
          interval,
          timezone: 'Etc/UTC',
          theme,
          style: '1',
          locale: 'en',
          toolbar_bg: '#f1f3f6',
          enable_publishing: false,
          withdateranges: true,
          hide_side_toolbar: false,
          allow_symbol_change: true,
          details: true,
          hotlist: true,
          calendar: true,
          studies: ['RSI@tv-basicstudies', 'MACD@tv-basicstudies', 'BB@tv-basicstudies'],
          container_id: containerRef.current.id,
        });
      }
    };
    document.head.appendChild(script);

    // Clean up
    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, [symbol, interval, theme, autosize]);

  return (
    <div className="w-full h-full">
      <div 
        id={`tradingview_${symbol.toLowerCase()}`} 
        ref={containerRef} 
        className={`w-full ${autosize ? 'h-full' : ''}`}
        style={{ height: autosize ? '100%' : `${height}px`, width: autosize ? '100%' : `${width}px` }}
      />
    </div>
  );
};

export default TradingViewChart;

// Add TradingView types
declare global {
  interface Window {
    TradingView: {
      widget: new (options: any) => any;
    };
  }
} 