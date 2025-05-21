/**
 * Utility functions for formatting various values in the application
 */

/**
 * Format a number as a currency value
 * @param value - Number to format
 * @param currency - Currency code (default: USD)
 * @param digits - Number of decimal places (default: 2)
 * @returns Formatted currency string
 */
export function formatCurrency(value: number, currency = 'USD', digits = 2): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

/**
 * Format a number as a percentage
 * @param value - Number to format (e.g., 0.05 for 5%)
 * @param digits - Number of decimal places (default: 2)
 * @returns Formatted percentage string
 */
export function formatPercent(value: number, digits = 2): string {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value / 100);
}

/**
 * Format a datetime string to a human-readable time
 * @param dateTimeString - ISO datetime string
 * @returns Formatted time string
 */
export function formatTime(dateTimeString: string): string {
  const date = new Date(dateTimeString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * Format a datetime string to a date
 * @param dateTimeString - ISO datetime string
 * @returns Formatted date string
 */
export function formatDate(dateTimeString: string): string {
  const date = new Date(dateTimeString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format a datetime string to a relative time (e.g., "5 minutes ago")
 * @param dateTimeString - ISO datetime string
 * @returns Relative time string
 */
export function formatRelativeTime(dateTimeString: string): string {
  const date = new Date(dateTimeString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  
  if (diffSeconds < 60) {
    return `${diffSeconds}s ago`;
  }
  
  const diffMinutes = Math.floor(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }
  
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

/**
 * Format a number with thousands separators
 * @param value - Number to format
 * @param digits - Number of decimal places (default: 2)
 * @returns Formatted number string
 */
export function formatNumber(value: number, digits = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

/**
 * Format a large number with abbreviations (K, M, B)
 * @param value - Number to format
 * @param digits - Number of decimal places (default: 1)
 * @returns Abbreviated number string
 */
export function formatCompactNumber(value: number, digits = 1): string {
  return new Intl.NumberFormat('en-US', {
    notation: 'compact',
    compactDisplay: 'short',
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

/**
 * Format a trade side (buy/sell) with appropriate styling class
 * @param side - Trade side ("buy" or "sell")
 * @returns CSS class name
 */
export function tradeSideClass(side: string): string {
  return side.toLowerCase() === 'buy' ? 'buy-color' : 'sell-color';
} 