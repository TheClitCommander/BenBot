import { useMutation } from '@tanstack/react-query';
import { submitTradierOrder } from "../services/tradierApi";

export function useTradierOrder() {
  return useMutation({
    mutationFn: (orderData: {
      account_id: string,
      symbol: string,
      qty: number,
      side: string
    }) => submitTradierOrder(orderData),
    onError: (error) => {
      console.error('Error submitting Tradier order:', error);
    }
  });
} 