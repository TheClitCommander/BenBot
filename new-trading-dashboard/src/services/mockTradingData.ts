// Mock data for trading components

// Safety Controls
export const mockSafetyStatus = {
  emergencyStopActive: false,
  tradingMode: "paper", // "paper" or "live"
  tradingAllowed: true,
  tradingBlockedReason: null,
  circuitBreakers: [
    {
      id: "daily_loss",
      name: "Daily Loss Limit",
      active: false,
      threshold: "-5%",
      current: "-1.2%",
      timeRemaining: null
    },
    {
      id: "volatility",
      name: "Market Volatility",
      active: false,
      threshold: "High",
      current: "Medium",
      timeRemaining: null
    }
  ],
  cooldowns: [
    {
      id: "consecutive_losses",
      name: "After 3 Losses",
      active: false,
      duration: "30m",
      timeRemaining: null
    }
  ]
};

// Safety Event History
export const mockSafetyEvents = [
  {
    id: "1",
    timestamp: "2023-05-14T08:30:00Z",
    type: "CIRCUIT_BREAKER",
    name: "Daily Loss Limit",
    description: "Circuit breaker triggered at -5.2% daily loss",
    status: "RESOLVED",
    duration: "2h 15m"
  },
  {
    id: "2",
    timestamp: "2023-05-13T14:45:00Z",
    type: "COOLDOWN",
    name: "After 3 Losses",
    description: "Cooldown period after 3 consecutive losing trades",
    status: "RESOLVED",
    duration: "30m"
  },
  {
    id: "3",
    timestamp: "2023-05-10T09:15:00Z",
    type: "EMERGENCY_STOP",
    name: "Manual Shutdown",
    description: "Emergency stop activated by user",
    status: "RESOLVED",
    duration: "4h 20m"
  }
];

// Performance Chart
export const mockPerformanceData = {
  initialCapital: 10000,
  currentEquity: 11250,
  returns: [
    { date: "2023-05-01", equity: 10000 },
    { date: "2023-05-02", equity: 10120 },
    { date: "2023-05-03", equity: 10080 },
    { date: "2023-05-04", equity: 10250 },
    { date: "2023-05-05", equity: 10310 },
    { date: "2023-05-08", equity: 10290 },
    { date: "2023-05-09", equity: 10450 },
    { date: "2023-05-10", equity: 10400 },
    { date: "2023-05-11", equity: 10600 },
    { date: "2023-05-12", equity: 10700 },
    { date: "2023-05-13", equity: 11050 },
    { date: "2023-05-14", equity: 11250 }
  ],
  metrics: {
    totalReturn: "12.5%",
    dailyReturn: "1.8%",
    sharpeRatio: 1.95,
    maxDrawdown: "-2.1%",
    winRate: "68%",
    profitFactor: 2.3,
    averageWin: "$120",
    averageLoss: "$70"
  }
};

// Position Table
export const mockPositions = [
  {
    id: "1",
    symbol: "AAPL",
    strategy: "Momentum Equity",
    entryPrice: 182.35,
    currentPrice: 187.80,
    quantity: 15,
    value: 2817.00,
    profitLoss: 81.75,
    profitLossPercent: 2.99,
    entryDate: "2023-05-10T09:32:00Z",
    status: "OPEN"
  },
  {
    id: "2",
    symbol: "MSFT",
    strategy: "Momentum Equity",
    entryPrice: 338.12,
    currentPrice: 352.70,
    quantity: 8,
    value: 2821.60,
    profitLoss: 116.64,
    profitLossPercent: 4.31,
    entryDate: "2023-05-12T14:22:00Z",
    status: "OPEN"
  },
  {
    id: "3",
    symbol: "BTC/USD",
    strategy: "Crypto Trend",
    entryPrice: 27350.50,
    currentPrice: 29125.80,
    quantity: 0.08,
    value: 2330.06,
    profitLoss: 142.02,
    profitLossPercent: 6.49,
    entryDate: "2023-05-13T08:15:00Z",
    status: "OPEN"
  }
];

// Signal Log
export const mockSignals = [
  {
    id: "1",
    timestamp: "2023-05-14T09:45:00Z",
    symbol: "AAPL",
    action: "BUY",
    price: 182.35,
    quantity: 15,
    strategy: "Momentum Equity",
    confidence: 0.82,
    status: "EXECUTED"
  },
  {
    id: "2",
    timestamp: "2023-05-14T09:48:00Z",
    symbol: "MSFT",
    action: "BUY",
    price: 338.12,
    quantity: 8,
    strategy: "Momentum Equity",
    confidence: 0.79,
    status: "EXECUTED"
  },
  {
    id: "3",
    timestamp: "2023-05-14T10:15:00Z",
    symbol: "NFLX",
    action: "BUY",
    price: 425.10,
    quantity: 6,
    strategy: "Momentum Equity",
    confidence: 0.68,
    status: "REJECTED"
  },
  {
    id: "4",
    timestamp: "2023-05-14T10:30:00Z",
    symbol: "BTC/USD",
    action: "BUY",
    price: 27350.50,
    quantity: 0.08,
    strategy: "Crypto Trend",
    confidence: 0.85,
    status: "EXECUTED"
  },
  {
    id: "5",
    timestamp: "2023-05-14T11:05:00Z",
    symbol: "ETH/USD",
    action: "BUY",
    price: 1820.25,
    quantity: 1.5,
    strategy: "Crypto Trend",
    confidence: 0.77,
    status: "PENDING"
  }
]; 