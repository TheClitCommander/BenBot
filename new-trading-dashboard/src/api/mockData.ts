import { Strategy } from '../hooks/useActiveStrategies';

// Mock data for metrics overview
export const overviewMetrics = {
  portfolio_value: 10245.8,
  portfolio_change_pct: 2.3,
  position_count: 2,
  position_value: 7250.5,
  strategy_count: 3,
  strategy_active_count: 2,
  daily_pnl: 230,
  daily_pnl_pct: 2.3,
  total_pnl: 1245.8,
  total_pnl_pct: 12.8,
};

// Mock data for risk metrics
export const riskMetrics = {
  max_drawdown: 8.2,
  max_drawdown_value: 840.5,
  sharpe_ratio: 1.85,
  sortino_ratio: 2.15,
  win_rate: 68.4,
  profit_factor: 2.3,
  var_daily_95: 340.5,
  var_daily_99: 520.7,
  margin_utilization: 42.5,
  max_leverage: 2.1,
  risk_allocation: [
    { strategy: 'BTC Trend Following', allocation: 35 },
    { strategy: 'ETH Mean Reversion', allocation: 40 },
    { strategy: 'Altcoin Momentum', allocation: 25 }
  ],
  market_exposure: [
    { market: 'BTCUSDT', long: 25, short: 0 },
    { market: 'ETHUSDT', long: 0, short: 30 },
    { market: 'SOLUSDT', long: 10, short: 0 },
  ],
  drawdown_history: [
    { date: '2025-04-15', value: 2.1 },
    { date: '2025-04-16', value: 3.4 },
    { date: '2025-04-17', value: 5.2 },
    { date: '2025-04-18', value: 8.2 },
    { date: '2025-04-19', value: 7.5 },
    { date: '2025-04-20', value: 4.3 },
    { date: '2025-04-21', value: 2.8 },
    { date: '2025-04-22', value: 1.5 },
    { date: '2025-04-23', value: 0.7 },
    { date: '2025-04-24', value: 1.2 },
  ]
};

// Mock data for system status
export const systemStatus = {
  status: 'active',
  cpu_usage: 24.5,
  memory_usage: 38.2,
  disk_usage: 55.3,
  uptime: '5d 12h 32m',
  last_reboot: '2025-05-10T08:15:00Z',
  strategy_usage: [
    { strategy: 'BTC Trend Following', cpu: 12.3, memory: 18.5 },
    { strategy: 'ETH Mean Reversion', cpu: 8.7, memory: 12.4 },
    { strategy: 'Altcoin Momentum', cpu: 3.5, memory: 7.3 }
  ],
  events: [
    { type: 'warning', message: 'High CPU usage detected', timestamp: '2025-05-15T10:23:00Z' },
    { type: 'info', message: 'System updated to version 1.2.5', timestamp: '2025-05-14T08:00:00Z' }
  ]
};

// Mock data for active strategies
export const activeStrategies: Strategy[] = [
  {
    id: 'strat-btc-trend-1',
    name: 'BTC Trend Following',
    market: 'BTCUSDT',
    status: 'active',
    type: 'trend',
    pnl_today_pct: 1.5,
    pnl_total_pct: 12.8,
    daily_pnl_pct: 1.5,
    total_pnl_pct: 12.8,
    position_count: 1,
    last_trade_time: '15m ago',
    created_at: '2025-04-15T12:00:00Z',
    current_value: 2450.75,
    parameters: {
      'lookback_period': 14,
      'ema_fast': 9,
      'ema_slow': 21,
      'risk_per_trade': '2%',
      'take_profit': '3%',
      'stop_loss': '2%'
    }
  },
  {
    id: 'strat-eth-reversion-1',
    name: 'ETH Mean Reversion',
    market: 'ETHUSDT',
    status: 'active',
    type: 'mean-reversion',
    pnl_today_pct: -0.8,
    pnl_total_pct: 5.2,
    daily_pnl_pct: -0.8,
    total_pnl_pct: 5.2,
    position_count: 1,
    last_trade_time: '2h ago',
    created_at: '2025-03-22T09:30:00Z',
    current_value: 3212.50,
    parameters: {
      'bollinger_length': 20,
      'bollinger_dev': 2,
      'rsi_period': 14,
      'rsi_oversold': 30,
      'rsi_overbought': 70,
      'position_size': '5%'
    }
  },
  {
    id: 'strat-alt-momentum-1',
    name: 'Altcoin Momentum',
    market: 'Multi',
    status: 'paused',
    type: 'momentum',
    pnl_today_pct: 0,
    pnl_total_pct: 7.9,
    daily_pnl_pct: 0,
    total_pnl_pct: 7.9,
    position_count: 0,
    last_trade_time: '1d 4h ago',
    created_at: '2025-04-05T15:45:00Z',
    current_value: 1215.00,
    parameters: {
      'momentum_period': 10,
      'vol_filter': true,
      'max_assets': 5,
      'rebalance_period': '24h',
      'min_volume': '1M USD'
    }
  }
];

// Mock data for positions
export const positions = [
  {
    id: 'pos-1',
    symbol: 'BTCUSDT',
    side: 'LONG',
    size: 0.1,
    entry_price: 44350.50,
    current_price: 45200.75,
    pnl_pct: 1.91,
    pnl_value: 85.02,
    age: '2d 4h',
    strategy_id: 'strat-btc-trend-1'
  },
  {
    id: 'pos-2',
    symbol: 'ETHUSDT',
    side: 'SHORT',
    size: 1.25,
    entry_price: 2570.00,
    current_price: 2520.50,
    pnl_pct: 2.42,
    pnl_value: 61.88,
    age: '14h',
    strategy_id: 'strat-eth-reversion-1'
  }
];

// Mock data for trades
export const trades = [
  {
    id: 'trade-1',
    time: '2025-05-15T12:15:00Z',
    symbol: 'BTCUSDT',
    side: 'BUY',
    size: 0.1,
    price: 44350.50,
    total: 4435.05,
    strategy: 'BTC Trend Following'
  },
  {
    id: 'trade-2',
    time: '2025-05-14T23:00:00Z',
    symbol: 'ETHUSDT',
    side: 'SELL',
    size: 1.25,
    price: 2570.00,
    total: 3212.50,
    strategy: 'ETH Mean Reversion'
  },
  {
    id: 'trade-3',
    time: '2025-05-14T21:30:00Z',
    symbol: 'SOLUSDT',
    side: 'BUY',
    size: 10,
    price: 121.50,
    total: 1215.00,
    strategy: 'Altcoin Momentum'
  }
];

// Mock data for markets
export const markets = [
  {
    symbol: 'BTCUSDT',
    price: 45200.75,
    change_pct: 1.92,
    volume: 32500000000,
    high_24h: 45500.00,
    low_24h: 44100.25
  },
  {
    symbol: 'ETHUSDT',
    price: 2520.50,
    change_pct: -0.75,
    volume: 18200000000,
    high_24h: 2580.00,
    low_24h: 2510.25
  },
  {
    symbol: 'SOLUSDT',
    price: 121.50,
    change_pct: 2.8,
    volume: 5700000000,
    high_24h: 123.75,
    low_24h: 118.50
  },
  {
    symbol: 'BNBUSDT',
    price: 602.75,
    change_pct: 0.65,
    volume: 2100000000,
    high_24h: 608.50,
    low_24h: 595.25
  }
];

// Mock market history data (for charts)
export const marketHistory = {
  BTCUSDT: Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 60 * 60 * 1000).toISOString(),
    price: 44000 + Math.random() * 1500
  })),
  ETHUSDT: Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 60 * 60 * 1000).toISOString(),
    price: 2500 + Math.random() * 100
  })),
  SOLUSDT: Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 60 * 60 * 1000).toISOString(),
    price: 118 + Math.random() * 8
  })),
  BNBUSDT: Array.from({ length: 24 }, (_, i) => ({
    timestamp: new Date(Date.now() - (23 - i) * 60 * 60 * 1000).toISOString(),
    price: 590 + Math.random() * 20
  }))
};

// Mock data for AI market analysis
export const marketContext = {
  analysis: {
    overall_sentiment: 5.2,
    market_conditions: "Markets are generally bullish with some sector rotation occurring.",
    key_events: [
      "Fed signaled potential pause in rate hikes",
      "Tech earnings exceeded expectations",
      "Inflation data showed slight decrease month-over-month"
    ],
    sector_analysis: {
      "Technology": "Leading the market with strong momentum",
      "Finance": "Performance is mixed with pressure from yield curve",
      "Energy": "Underperforming due to commodity price fluctuations"
    },
    risk_factors: [
      "Geopolitical tensions in Eastern Europe",
      "Supply chain constraints persisting in key industries",
      "Potential policy shifts from upcoming elections"
    ],
    opportunities: [
      "AI and semiconductor stocks showing strong momentum",
      "Healthcare innovation driven by new treatments",
      "Renewable energy expansion supported by policy incentives"
    ],
    outlook: "Cautiously optimistic with higher volatility expected"
  },
  raw_data: {
    news_count: 124,
    symbols_analyzed: ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"],
    economic_indicators: {
      "unemployment_rate": 3.8,
      "inflation_rate": 2.4,
      "gdp_growth": 2.1,
      "fed_rate": 5.25
    }
  },
  generated_at: new Date().toISOString(),
  data_window_days: 14
};

// Mock account info for Alpaca
export const accountInfo = {
  id: 'mock-account-id-12345',
  account_number: 'ABC12345',
  status: 'ACTIVE',
  currency: 'USD',
  cash: 10000.75,
  portfolio_value: 25650.42,
  buying_power: 20000.50,
  equity: 25650.42,
  pattern_day_trader: false,
  trading_blocked: false,
  transfers_blocked: false,
  account_blocked: false,
  created_at: '2023-01-15T16:35:21Z',
  trade_suspended_by_user: false,
  multiplier: '4',
  shorting_enabled: true,
  daytrade_count: 0,
  daytrading_buying_power: 75000.25,
  regt_buying_power: 50000.42,
}; 