import { useState, useEffect } from 'react';
import { apiService } from '../api/client';

// Hook for fetching live price data
export function useLivePrice(symbol: string, refreshInterval = 5000) {
  const [price, setPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isSubscribed = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await apiService.getLivePrice(symbol);
        if (isSubscribed) {
          setPrice(response.data.price);
          setError(null);
        }
      } catch (err) {
        if (isSubscribed) {
          setError(`Failed to fetch price for ${symbol}: ${err instanceof Error ? err.message : String(err)}`);
        }
      } finally {
        if (isSubscribed) {
          setLoading(false);
        }
      }
    };

    fetchData();
    
    // Set up interval to refresh data
    const intervalId = setInterval(fetchData, refreshInterval);
    
    // Cleanup
    return () => {
      isSubscribed = false;
      clearInterval(intervalId);
    };
  }, [symbol, refreshInterval]);

  return { price, loading, error };
}

// Hook for fetching live account data
export function useLiveAccount(refreshInterval = 10000) {
  const [account, setAccount] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isSubscribed = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await apiService.getLiveAccount();
        if (isSubscribed) {
          setAccount(response.data);
          setError(null);
        }
      } catch (err) {
        if (isSubscribed) {
          setError(`Failed to fetch account data: ${err instanceof Error ? err.message : String(err)}`);
        }
      } finally {
        if (isSubscribed) {
          setLoading(false);
        }
      }
    };

    fetchData();
    
    // Set up interval to refresh data
    const intervalId = setInterval(fetchData, refreshInterval);
    
    // Cleanup
    return () => {
      isSubscribed = false;
      clearInterval(intervalId);
    };
  }, [refreshInterval]);

  return { account, loading, error };
}

// Hook for fetching live positions
export function useLivePositions(refreshInterval = 10000) {
  const [positions, setPositions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isSubscribed = true;
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await apiService.getLivePositions();
        if (isSubscribed) {
          setPositions(response.data);
          setError(null);
        }
      } catch (err) {
        if (isSubscribed) {
          setError(`Failed to fetch positions: ${err instanceof Error ? err.message : String(err)}`);
        }
      } finally {
        if (isSubscribed) {
          setLoading(false);
        }
      }
    };

    fetchData();
    
    // Set up interval to refresh data
    const intervalId = setInterval(fetchData, refreshInterval);
    
    // Cleanup
    return () => {
      isSubscribed = false;
      clearInterval(intervalId);
    };
  }, [refreshInterval]);

  return { positions, loading, error };
}

// Order submission hook
export function useOrderSubmission() {
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitOrder = async (orderData: {
    symbol: string;
    side: string;
    qty: number;
    type?: string;
    limit_price?: number;
  }) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiService.submitOrder(orderData);
      setResponse(result.data);
      return result.data;
    } catch (err) {
      const errorMessage = `Failed to submit order: ${err instanceof Error ? err.message : String(err)}`;
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return { submitOrder, response, loading, error };
} 